import logging
from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import time
import pytz
import asyncpg
import re
from typing import Optional
import config as cf
from src.analytics.api import get_reports, get_reports_from_state
from src.analytics.constant.urls import all_report_urls
from src.analytics.db.db import get_report_hint_text
from src.analytics.handlers.text.recommendations import recommendations
from src.analytics.handlers.text.revenue_texts import revenue_analysis_text, revenue_recommendations
from src.analytics.handlers.text.texts import text_functions
from src.analytics.handlers.types.text_data import TextData
from src.analytics.constant.variants import all_departments, all_branches, all_types, all_periods
from src.basic.commands.start_command import start_handler
from src.mailing.commands.registration.notifications.keyboards import get_main_menu_keyboard

# Инициализация планировщика
scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Moscow"))
DB_CONFIG = cf.DB_CONFIG

subscription_router = Router()

@subscription_router.callback_query(F.data == "main_menu")
async def handle_main_menu_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()  # Закрываем спиннер на кнопке
    await start_handler(callback.from_user.id, callback.message, state)


async def get_department_name(tgid: int, department_id: str) -> str:
    departments = await all_departments(tgid)
    return departments.get(department_id, department_id)


async def generate_report(
        tgid: int,
        state_data: dict,
        type_prefix: str = "",
        only_negative: bool = False,
        recommendations: bool = False
) -> list[str]:
    report_type = state_data.get("report:type")
    format_type = state_data.get("report:format_type", "")
    period = state_data.get("report:period")
    department_uuid = state_data.get("report:department")
    department = str(department_uuid) if department_uuid else None

    # Определяем тип обработки на основе format_type
    is_recommendations = format_type == "recommendations"
    is_analysis = format_type == "analysis" or format_type.startswith("analysis_")

    # Проверка наличия URL для отчета
    if report_type not in all_report_urls:
        available_reports = "\n".join([f"- {k}" for k in all_report_urls.keys()])
        raise ValueError(
            f'Для типа отчета "{report_type}" не настроен URL.\n'
            f'Доступные типы отчетов:\n{available_reports}'
        )

    # Определяем префикс в зависимости от типа отчета
    used_prefix = ""
    if is_analysis:
        used_prefix = "analysis."
    elif is_recommendations and report_type == "revenue":
        used_prefix = "recommendations."

    reports = await get_reports_from_state(tgid=tgid, state_data=state_data, type_prefix=used_prefix)

    if None in reports:
        raise ValueError("Не удалось загрузить данные для отчёта.")

    # Получаем функцию для формирования текста
    text_func_key = used_prefix + report_type
    text_func = text_functions.get(text_func_key)
    if not text_func:
        raise ValueError(f"Нет функции обработки текста для отчёта '{report_type}' с префиксом '{used_prefix}'")

    text_data = TextData(reports=reports, period=period, department=department,
                         only_negative=is_analysis and "only_negative" in format_type)

    # Генерируем текст
    texts = text_func(text_data)

    # Добавляем рекомендации если нужно
    if is_recommendations and report_type == "revenue":
        texts.extend(revenue_analysis_text(text_data, msg_type="revenue_recomendations"))

    return texts


async def get_subscriptions_from_db():
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        result = await conn.fetch(''' 
            SELECT user_id, subscription_type, periodicity, weekday, day_of_month, time, timezone_offset, 
                   date_periodity, department, report_type, menu_buttons as format_type
            FROM subscriptions 
            WHERE periodicity IN ('daily', 'weekly', 'monthly')
        ''')
        logging.info(f"Получено {len(result)} подписок из базы данных.")
        return result
    except Exception as e:
        logging.error(f"Ошибка при получении подписок: {e}")
        return []
    finally:
        await conn.close()

async def add_subscription_task(
    bot: Bot,
    user_id: int,
    sub_type: str,
    periodicity: str,
    weekday: Optional[int],
    day_of_month: Optional[int],
    time_obj: time,
    date_periodity: str,
    report_type: str,
    department: str,
    menu_buttons: str = ""  # Используем menu_buttons вместо format_type
):
    hour, minute = time_obj.hour, time_obj.minute
    logging.info(f"Добавление задачи для пользователя {user_id} на {hour}:{minute} для отчёта {sub_type}.")

    if periodicity == "daily":
        trigger = CronTrigger(hour=hour, minute=minute, timezone=pytz.timezone("Europe/Moscow"))
    elif periodicity == "weekly":
        trigger = CronTrigger(day_of_week=weekday, hour=hour, minute=minute, timezone=pytz.timezone("Europe/Moscow"))
    elif periodicity == "monthly":
        trigger = CronTrigger(day=day_of_month, hour=hour, minute=minute, timezone=pytz.timezone("Europe/Moscow"))
    elif periodicity == "workdays":
        trigger = CronTrigger(day_of_week='mon-fri', hour=hour, minute=minute, timezone=pytz.timezone("Europe/Moscow"))
    else:
        raise ValueError(f"Неизвестная периодичность: {periodicity}")

    scheduler.add_job(
        send_report,
        trigger,
        args=[bot, user_id, report_type, date_periodity, department, menu_buttons],  # Передаем menu_buttons
        id=f"report_{user_id}_{sub_type}_{periodicity}_{hour}_{minute}",
        replace_existing=True
    )
    logging.info(f"Задача для пользователя {user_id} успешно добавлена в планировщик.")


async def send_report(
        bot: Bot,
        user_id: int,
        report_type: str,
        date_periodity: str,
        department: str,
        format_type: str = ""
):
    logging.info(
        f"Отправка отчёта для пользователя {user_id}, отчет: {report_type}, период: {date_periodity}, формат: {format_type}"
    )

    try:
        state_data = {
            "report:type": report_type,
            "report:period": date_periodity,
            "report:department": department,
            "report:format_type": format_type
        }

        department_name = await get_department_name(user_id, department)

        # Получаем русские названия отчёта и периода
        report_name = all_branches.get(report_type) or all_types.get(report_type, report_type)
        period_name = all_periods.get(date_periodity, date_periodity)

        # Формируем заголовок
        header = (
            f"📊 <b>Отчёт:</b> {report_name}\n"
            f"📅 <b>Период:</b> {period_name}\n"
            f"📍 <b>Объект:</b> {department_name}\n\n"
        )

        # === Обработка формата рекомендаций ===
        if format_type == "recommendations":
            if report_type == "revenue":
                reports = await get_reports_from_state(tgid=user_id, state_data=state_data, type_prefix="analysis.")
                if None in reports:
                    await bot.send_message(
                        user_id,
                        header + "Не удалось загрузить данные для отчёта.",
                        parse_mode="HTML",
                        reply_markup=get_main_menu_keyboard()
                    )
                    return

                text_data = TextData(reports=reports, period=date_periodity, department=department, only_negative=True)
                texts = revenue_analysis_text(text_data, recommendations=True)

                if not texts:
                    await bot.send_message(
                        user_id,
                        header + "Рекомендации не найдены.",
                        parse_mode="HTML",
                        reply_markup=get_main_menu_keyboard()
                    )
                    return

                for i, text in enumerate(texts):
                    is_html = bool(re.search(r"</?\w+.*?>", text))
                    parse_mode = "HTML" if is_html else "Markdown"

                    if i == 0 and not any(tag in text for tag in ["📍", "📊", "📅", "<b>Объект", "<code>Объект"]):
                        text = header + text
                    await bot.send_message(user_id, text, parse_mode=parse_mode)

                # Добавляем сообщение со ссылкой
                report_hint = await get_report_hint_text(user_id, report_type, format_type)
                if report_hint:
                    hint_text = f"<b>🔗 Подробнее:</b> <a href='{report_hint['url']}'>{report_hint['description']}</a>"
                    await bot.send_message(user_id, hint_text, parse_mode="HTML")

                await bot.send_message(
                    user_id,
                    "Рекомендации успешно отправлены. Вы можете вернуться в главное меню:",
                    reply_markup=get_main_menu_keyboard()
                )

                logging.info(f"Рекомендации по revenue отчёту успешно отправлены пользователю {user_id}.")
                return
            else:
                # Обработка других типов отчётов
                recommendations_text = recommendations.get(report_type, "")
                if recommendations_text:
                    await bot.send_message(
                        user_id,
                        header + "<b>Рекомендации:</b>\n" + recommendations_text,
                        parse_mode="HTML",
                        reply_markup=get_main_menu_keyboard()
                    )

                    # Добавляем сообщение со ссылкой
                    report_hint = await get_report_hint_text(user_id, report_type, format_type)
                    if report_hint:
                        hint_text = f"<b>🔗 Подробнее:</b> <a href='{report_hint['url']}'>{report_hint['description']}</a>"
                        await bot.send_message(user_id, hint_text, parse_mode="HTML")

                    logging.info(f"Рекомендации по отчёту {report_type} успешно отправлены пользователю {user_id}.")
                    return
                else:
                    await bot.send_message(
                        user_id,
                        header + "Для данного типа отчёта рекомендации не найдены.",
                        parse_mode="HTML",
                        reply_markup=get_main_menu_keyboard()
                    )
                    return

        # === Генерация обычного отчёта ===
        texts = await generate_report(tgid=user_id, state_data=state_data)

        for i, text in enumerate(texts):
            is_html = bool(re.search(r"</?\w+.*?>", text))
            parse_mode = "HTML" if is_html else "Markdown"

            if i == 0:
                if any(tag in text for tag in ["📍", "📊", "📅", "<b>Объект", "<code>Объект"]):
                    await bot.send_message(user_id, text, parse_mode=parse_mode)
                else:
                    await bot.send_message(user_id, header + text, parse_mode=parse_mode)
            else:
                await bot.send_message(user_id, text, parse_mode=parse_mode)

        # Добавляем сообщение со ссылкой после основного отчета
        report_hint = await get_report_hint_text(user_id, report_type, format_type)
        if report_hint:
            hint_text = f"<b>🔗 Подробнее:</b> <a href='{report_hint['url']}'>{report_hint['description']}</a>"
            await bot.send_message(user_id, hint_text, parse_mode="HTML")

        await bot.send_message(
            user_id,
            "Отчёт успешно сформирован. Вы можете вернуться в главное меню:",
            reply_markup=get_main_menu_keyboard()
        )

        logging.info(f"Отчёт {report_type} успешно отправлен пользователю {user_id}.")

    except Exception as e:
        logging.error(f"Ошибка при отправке отчёта пользователю {user_id}: {e}")
        await bot.send_message(
            user_id,
            "Произошла ошибка при отправке отчёта. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )


async def schedule_all_subscriptions(bot: Bot):
    subscriptions = await get_subscriptions_from_db()
    for sub in subscriptions:
        if not sub.get('report_type'):
            logging.error(f"Отсутствует report_type для подписки пользователя {sub['user_id']}")
            continue

        await add_subscription_task(
            bot=bot,
            user_id=sub['user_id'],
            sub_type=sub['subscription_type'],
            periodicity=sub['periodicity'],
            weekday=sub['weekday'],
            day_of_month=sub['day_of_month'],
            time_obj=sub['time'],
            date_periodity=sub['date_periodity'],
            report_type=sub['report_type'],
            department=sub['department'],
            menu_buttons=sub.get('format_type', '')  # Используем format_type из результата запроса
        )


def start_scheduler():
    scheduler.start()
    logging.info("Планировщик запущен.")


logging.basicConfig(level=logging.INFO)
