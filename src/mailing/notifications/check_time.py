import logging
from datetime import time
from typing import Optional, Any
import pytz
import asyncpg
from asyncpg.exceptions import PostgresError
from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import config as cf
from src.analytics.constant.urls import all_report_urls

# Инициализация планировщика
scheduler = AsyncIOScheduler()

router = Router()
DB_CONFIG = cf.DB_CONFIG


class SubscriptionStates(StatesGroup):
    choosing_frequency = State()
    choosing_type = State()
    choosing_day = State()
    choosing_timezone = State()
    choosing_weekday = State()
    choosing_day_of_month = State()
    choosing_monthly_day = State()
    choosing_time = State()


def format_report_links(report_type: str) -> str:
    if report_type not in all_report_urls:
        return ""
    sub_reports = all_report_urls[report_type]
    link_lines = []
    for sub_type in sub_reports:
        readable_name = sub_type.split(":")[-1].replace("_", " ").capitalize()
        link_lines.append(f"🔗 <b>{readable_name}:</b> /{sub_type}")
    return "\n\n" + "\n".join(link_lines) if link_lines else ""


async def generate_report_text(report_type: str) -> str:
    return f"📊 Текстовый отчет: <b>{report_type}</b>\nДанные за текущий период..."


async def get_subscriptions_from_db() -> list[dict]:
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        records = await conn.fetch("""
            SELECT 
                user_id, 
                subscription_type, 
                periodicity, 
                weekday, 
                day_of_month, 
                time::text as time_str,
                timezone_offset, 
                report_type,
                token,
                date_periodity,
                department,
                report_format
            FROM subscriptions 
            WHERE periodicity IN ('daily', 'weekly', 'monthly')
              AND is_active = true;
        """)
        subscriptions = []
        for record in records:
            try:
                time_parts = list(map(int, record['time_str'].split(':')))
                time_obj = time(time_parts[0], time_parts[1])
                subscriptions.append({
                    'user_id': record['user_id'],
                    'subscription_type': record['subscription_type'],
                    'periodicity': record['periodicity'],
                    'weekday': record['weekday'],
                    'day_of_month': record['day_of_month'],
                    'time': time_obj,
                    'timezone_offset': int(record['timezone_offset']),
                    'report_type': record['report_type'],
                    'token': record['token'],
                    'date_periodity': record.get('date_periodity', 'daily'),
                    'department': record.get('department', ''),
                    'report_format': record.get('report_format', 'text')
                })
            except Exception as e:
                logging.error(f"Ошибка обработки подписки {record}: {e}")
        return subscriptions
    except PostgresError as e:
        logging.error(f"Ошибка БД при получении подписок: {e}")
        return []
    finally:
        if 'conn' in locals():
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
    timezone_offset: int,
    report_format: str
) -> bool:
    try:
        tz_str = f"Etc/GMT{'-' if timezone_offset >= 0 else '+'}{abs(timezone_offset)}"
        timezone = pytz.timezone(tz_str)
        hour, minute = time_obj.hour, time_obj.minute
        job_id = f"sub_{user_id}_{sub_type}_{periodicity}_{hour}_{minute}"

        if periodicity == 'daily':
            trigger = CronTrigger(hour=hour, minute=minute, timezone=timezone)
        elif periodicity == 'weekly':
            trigger = CronTrigger(day_of_week=weekday, hour=hour, minute=minute, timezone=timezone)
        else:
            trigger = CronTrigger(day=day_of_month, hour=hour, minute=minute, timezone=timezone)

        scheduler.add_job(
            send_text_report,
            trigger,
            args=[bot, user_id, report_type, report_format],
            id=job_id,
            replace_existing=True,
            misfire_grace_time=3600
        )
        logging.info(f"Задача {job_id} успешно добавлена.")
        return True
    except Exception as e:
        logging.error(f"Ошибка создания задачи: {e}", exc_info=True)
        return False


async def send_text_report(bot: Bot, tg_id: int, report_type: str, report_format: str):
    from src.analytics.db.db import get_report_hint_text
    try:
        # Генерируем основной текст отчета
        report_text = await generate_report_text(report_type)
        links_text = format_report_links(report_type)

        # Получаем данные для подписи с ссылкой
        hint = await get_report_hint_text(tg_id=tg_id, report_type=report_type, report_format=report_format)

        # Отправляем основной текст отчета
        await bot.send_message(
            chat_id=tg_id,
            text=f"{report_text}{links_text}",
            parse_mode="HTML"
        )

        # Отправляем отдельное сообщение с подписью и ссылкой (если есть данные)
        if hint:
            hint_text = (
                f"<b>📎 {hint['description']}</b>\n"
                f"<a href=\"{hint['url']}\">Скачать полный отчет</a>"
            )
            await bot.send_message(
                chat_id=tg_id,
                text=hint_text,
                parse_mode="HTML"
            )

    except Exception as e:
        logging.error(f"Ошибка при отправке отчета: {e}")
        await bot.send_message(
            chat_id=tg_id,
            text="⚠️ Произошла ошибка при формировании отчета"
        )


async def schedule_all_subscriptions(bot: Bot):
    subscriptions = await get_subscriptions_from_db()
    if not subscriptions:
        logging.warning("Нет активных подписок.")
        return

    success_count = 0
    for sub in subscriptions:
        result = await add_subscription_task(
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
            timezone_offset=sub['timezone_offset'],
            report_format=sub['report_format']
        )
        if result:
            success_count += 1

    logging.info(f"Запланировано задач: {success_count}/{len(subscriptions)}")


async def save_subscription(
    bot: Bot,
    user_id: int,
    sub_type: str,
    periodicity: str,
    weekday: Optional[int],
    day_of_month: Optional[int],
    time_obj: time,
    timezone_offset: int,
    report_type: str,
    date_periodity: str,
    department: str,
    token: str,
    report_format: str
) -> bool:
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        await conn.execute('''
            INSERT INTO subscriptions (
                user_id, subscription_type, periodicity, 
                weekday, day_of_month, time, timezone_offset,
                report_type, date_periodity, department, 
                token, is_active, report_format
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, true, $12)
            ON CONFLICT (user_id, subscription_type)
            DO UPDATE SET
                periodicity = EXCLUDED.periodicity,
                weekday = EXCLUDED.weekday,
                day_of_month = EXCLUDED.day_of_month,
                time = EXCLUDED.time,
                timezone_offset = EXCLUDED.timezone_offset,
                report_type = EXCLUDED.report_type,
                date_periodity = EXCLUDED.date_periodity,
                department = EXCLUDED.department,
                token = EXCLUDED.token,
                is_active = true,
                report_format = EXCLUDED.report_format,
                updated_at = NOW();
        ''', user_id, sub_type, periodicity, weekday, day_of_month, time_obj,
             timezone_offset, report_type, date_periodity, department, token, report_format)

        return await add_subscription_task(
            bot=bot,
            user_id=user_id,
            sub_type=sub_type,
            periodicity=periodicity,
            weekday=weekday,
            day_of_month=day_of_month,
            time_obj=time_obj,
            date_periodity=date_periodity,
            report_type=report_type,
            department=department,
            timezone_offset=timezone_offset,
            report_format=report_format
        )
    except PostgresError as e:
        logging.error(f"Ошибка при сохранении подписки: {e}")
        return False
    finally:
        if 'conn' in locals():
            await conn.close()


@router.message(SubscriptionStates.choosing_time)
async def handle_time_input(message: Message, state: FSMContext):
    try:
        hour, minute = map(int, message.text.strip().split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError()
        await state.update_data(time_obj=time(hour, minute))
        data = await state.get_data()

        success = await save_subscription(
            bot=message.bot,
            user_id=message.from_user.id,
            sub_type=data['sub_type'],
            periodicity=data['periodicity'],
            weekday=data.get('weekday'),
            day_of_month=data.get('day_of_month'),
            time_obj=time(hour, minute),
            timezone_offset=data['timezone_offset'],
            report_type=data['report_type'],
            date_periodity=data['date_periodity'],
            department=data.get('department', ''),
            token=data.get('token', ''),
            report_format=data.get('report_format', 'text')
        )
        if success:
            await message.answer(
                "✅ Подписка успешно оформлена!\n"
                f"• Тип отчета: {data['report_type']}\n"
                f"• Периодичность: {data['periodicity']}\n"
                f"• Время: {hour:02d}:{minute:02d}"
            )
        else:
            await message.answer("⚠️ Не удалось оформить подписку.")
        await state.clear()
    except ValueError:
        await message.answer("⚠️ Введите время в формате ЧЧ:ММ (например, 14:30)")


async def fetch_one(query: str, *args) -> Optional[dict[str, Any]]:
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None
    except PostgresError as e:
        logging.error(f"Ошибка БД: {e}")
        return None
    finally:
        if 'conn' in locals():
            await conn.close()

