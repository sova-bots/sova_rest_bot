import logging
import re
from typing import Optional

from aiogram import Dispatcher, Router, F, Bot
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import asyncpg
import config as cf
from datetime import datetime

from src.analytics.handlers.types.msg_data import MsgData
from src.basic.commands.start_command import start_handler
from src.mailing.commands.registration.notifications.keyboards import get_main_menu_keyboard
from src.mailing.notifications.keyboards import periodicity_kb, timezone_kb, all_periods, weekdays_kb
from src.analytics.constant.variants import all_departments, all_types, all_menu_buttons, menu_button_translations, all_time_periods
from src.mailing.commands.registration.notifications.check_time import generate_report, add_subscription_task

from src.mailing.commands.registration.notifications.check_time import scheduler

dp_mail = Dispatcher()

save_time_router = Router()

waiting_for_question = set()


class MailingStates(StatesGroup):
    waiting_for_time = State()


class Form(StatesGroup):
    choosing_time = State()


class SubscriptionState(StatesGroup):
    choosing_frequency = State()
    choosing_type = State()
    choosing_day = State()
    choosing_timezone = State()
    choosing_monthly_day = State()
    choosing_period = State()
    choosing_time = State()
    choosing_department = State()


DB_CONFIG = cf.DB_CONFIG

logging.basicConfig(level=logging.INFO)

router = Router(name=__name__)


async def init_db_pool():
    DB_URL = cf.DB_LINK
    return await asyncpg.create_pool(DB_URL)


db_pool = None


async def check_state_data(state: FSMContext):
    data = await state.get_data()
    logging.info(f"Текущее состояние: {data}")


@save_time_router.callback_query(F.data == "main_menu")
async def handle_main_menu_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()  # Удаляем сообщение с кнопкой
    await callback.answer()  # Закрываем спиннер
    await start_handler(callback.from_user.id, callback.message, state)  # Показываем главное меню



@save_time_router.callback_query(F.data == 'register_mailing')
async def subscribe_to_mailing(callback_query: CallbackQuery, state: FSMContext):
    keyboard = periodicity_kb
    await callback_query.message.answer("Выберите периодичность рассылки:", reply_markup=keyboard)


@save_time_router.callback_query(F.data.in_(all_periods.keys()))
async def choose_period(callback_query: CallbackQuery, state: FSMContext):
    period_key = callback_query.data  # Получаем ключ периода (например, "last-day")
    await state.update_data(**{"report:period": period_key})  # Сохраняем ключ периода в состояние

    logging.info(f"Пользователь {callback_query.from_user.id} выбрал период: {period_key}")

    # Переходим к следующему шагу (например, выбору времени)
    await state.set_state(SubscriptionState.choosing_time)
    await callback_query.message.answer("Теперь введите время рассылки в формате HH:MM.")


@save_time_router.callback_query(F.data.startswith("department_"))
async def process_department_choice(callback_query: CallbackQuery, state: FSMContext):
    department_choice = callback_query.data.split("_")[1]

    if department_choice == "all":
        await state.update_data(
            report_all_departments=True,
            report_department=None  # Очищаем конкретный выбор
        )
        await callback_query.answer("Выбраны все подразделения сети")
    else:
        await state.update_data(
            report_all_departments=False,
            report_department=department_choice
        )
        await callback_query.answer(f"Выбрано подразделение {department_choice}")

    await state.set_state(SubscriptionState.choosing_type)
    await callback_query.message.answer("Теперь выберите тип отчета.")



@save_time_router.callback_query(F.data.startswith("sub_"))
async def choose_subscription_type(callback_query: CallbackQuery, state: FSMContext):
    sub_type = callback_query.data.split("_")[1]
    logging.info(f"Пользователь {callback_query.from_user.id} выбрал периодичность: {sub_type}")

    await state.update_data(sub_type=sub_type)

    data = await state.get_data()
    report_type = data.get("report:type")

    if not report_type:
        logging.error("Тип отчёта не выбран в состоянии!")
        await callback_query.answer("Ошибка: тип отчёта не выбран. Пожалуйста, выберите тип отчёта.")
        return

    logging.info(f"Состояние перед выбором периодичности: {data}")
    logging.info(f"Выбранный тип отчета: {report_type}")

    await callback_query.answer(f"Вы выбрали периодичность: {sub_type} для отчёта: {report_type}")

    await callback_query.message.answer("Выберите ваш часовой пояс:", reply_markup=timezone_kb)


@save_time_router.callback_query(F.data.startswith("tz_"))
async def choose_timezone(callback_query: CallbackQuery, state: FSMContext):
    timezone_offset = int(callback_query.data.split("_")[1])
    await state.update_data(timezone_offset=timezone_offset)

    data = await state.get_data()
    sub_type = data.get("sub_type")

    if sub_type == "weekly":

        await state.set_state(SubscriptionState.choosing_day)
        days_kb = weekdays_kb
        await callback_query.message.answer("Выберите день недели:", reply_markup=days_kb)
    elif sub_type == "monthly":

        await state.set_state(SubscriptionState.choosing_monthly_day)
        await callback_query.message.answer("Введите число месяца (от 1 до 31), в которое хотите получать рассылку.")
    else:

        await state.set_state(SubscriptionState.choosing_time)
        await callback_query.message.answer("Теперь введите время рассылки в формате HH:MM.")


@save_time_router.callback_query(F.data.startswith("day_"))
async def choose_weekday(callback_query: CallbackQuery, state: FSMContext):
    weekday = int(callback_query.data.split("_")[1])
    await state.update_data(weekday=weekday)

    logging.info(f"Selected weekday: {weekday}")

    await state.set_state(SubscriptionState.choosing_time)
    await callback_query.message.answer("Теперь введите время рассылки в формате HH:MM.")


@save_time_router.message(SubscriptionState.choosing_day)
async def choose_weekday_or_day(message: Message, state: FSMContext):
    try:
        value = int(message.text)
        data = await state.get_data()
        logging.info(f"Received data: {data}")

        if "weekly" in data:
            if value < 0 or value > 6:
                raise ValueError("В неделе только дни с 0 (понедельник) до 6 (воскресенье).")
            await state.update_data(weekday=value)
            logging.info(f"Updated data with weekday={value}. State: {await state.get_data()}")
            await message.answer("Теперь выберите время рассылки в формате HH:MM.")
            await state.set_state(SubscriptionState.choosing_time)
        elif "monthly" in data:
            if value < 1 or value > 31:
                raise ValueError("В месяце только числа с 1 по 31.")
            await state.update_data(day_of_month=value)
            logging.info(f"Updated data with day_of_month={value}. State: {await state.get_data()}")
            await message.answer("Теперь выберите время рассылки в формате HH:MM.")
            await state.set_state(SubscriptionState.choosing_time)
    except ValueError as e:
        await message.answer(str(e))


@save_time_router.message(SubscriptionState.choosing_day)
async def choose_weekday(message: Message, state: FSMContext):
    days_of_week = {
        "Понедельник": 0, "Вторник": 1, "Среда": 2, "Четверг": 3, "Пятница": 4, "Суббота": 5, "Воскресенье": 6
    }
    day_text = message.text.strip()

    if day_text not in days_of_week:
        await message.answer("Пожалуйста, выберите день недели из списка.")
        return

    await state.update_data(weekday=days_of_week[day_text])
    logging.info(f"Selected weekday: {day_text} ({days_of_week[day_text]})")

    await message.answer("Теперь введите время рассылки в формате HH:MM.")
    await state.set_state(SubscriptionState.choosing_time)


@save_time_router.message(SubscriptionState.choosing_monthly_day)
async def choose_day_of_month(message: Message, state: FSMContext):
    """Обработчик выбора дня месяца для подписки"""
    try:
        day = int(message.text.strip())
        logging.info(f"User {message.from_user.id} is trying to set day: {day}")

        if 1 <= day <= 31:
            await state.update_data(day_of_month=day)
            await state.set_state(SubscriptionState.choosing_time)
            await message.answer("Теперь введите время рассылки в формате HH:MM.")
            logging.info(f"User {message.from_user.id} successfully set day of month to {day}.")
        else:
            await message.answer("Введите корректное число от 1 до 31.")
            logging.warning(f"User {message.from_user.id} entered invalid day value: {message.text}")
    except ValueError:
        await message.answer("Введите число месяца цифрами (например, 15).")
        logging.error(f"User {message.from_user.id} entered invalid day value: {message.text}")


@save_time_router.callback_query(F.data == 'show_subscriptions')
async def show_subscriptions(callback_query: CallbackQuery):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        subscriptions = await conn.fetch(''' 
            SELECT subscription_type, periodicity, weekday, day_of_month, time, department, report_type
            FROM subscriptions
            WHERE user_id = $1
        ''', callback_query.from_user.id)

        if not subscriptions:
            await callback_query.message.delete()
            await callback_query.message.answer(
                "Вы не подписаны ни на одну рассылку.",
                reply_markup=get_main_menu_keyboard()
            )
            return

        buttons = []
        for sub in subscriptions:
            report_type_key = sub['report_type']
            report_type_name = all_types.get(report_type_key, f"❓ {report_type_key}")
            period_name = all_time_periods.get(sub['periodicity'], sub['periodicity'])

            subscription_text = f"{report_type_name}, {period_name}"

            if sub['weekday'] is not None:
                weekday_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
                subscription_text += f", {weekday_names[sub['weekday']]}"

            if sub['day_of_month'] is not None:
                subscription_text += f", {sub['day_of_month']} число"

            subscription_text += f", {sub['time']}"

            buttons.append([
                InlineKeyboardButton(
                    text=subscription_text,
                    callback_data=f"subscription_{sub['subscription_type']}_{sub['time']}"
                )
            ])

        # Добавляем кнопку главного меню
        buttons.append([
            InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="main_menu")
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await callback_query.message.delete()  # Удаляем старое сообщение
        await callback_query.message.answer("📋 Ваши подписки:", reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Ошибка при извлечении подписок: {e}")
        await callback_query.message.answer(
            "Произошла ошибка при извлечении подписок. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        await conn.close()


async def execute_db_query(query: str, *args):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        return await conn.fetch(query, *args)
    except Exception as e:
        logging.error(f"DB error: {e}")
        return None
    finally:
        await conn.close()


@save_time_router.callback_query(F.data.startswith("unsubscribe_"))
async def unsubscribe(callback_query: CallbackQuery, bot: Bot):
    subscription_data = callback_query.data.split("_")

    if len(subscription_data) < 3:
        await callback_query.message.answer("Невозможно получить данные для отмены подписки.")
        return

    subscription_type = subscription_data[1]
    time_str = subscription_data[2]

    print(f"Полученные данные: subscription_type={subscription_type}, time_str={time_str}")

    try:
        if len(time_str) > 5:
            time_str = time_str[:5]  # Обрезаем до HH:MM

        time_obj = datetime.strptime(time_str, '%H:%M').time()
        sql_time_str = f"{time_obj.hour:02d}:{time_obj.minute:02d}:00"
    except ValueError:
        await callback_query.message.answer(f"Некорректное время для подписки: {time_str}. Ожидаемый формат - HH:MM.")
        return

    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        delete_count = await conn.execute('''
            DELETE FROM subscriptions 
            WHERE user_id = $1 AND subscription_type = $2 AND time = $3
        ''', callback_query.from_user.id, subscription_type, time_obj)

        if delete_count == "DELETE 0":
            await callback_query.message.answer(f"Подписка на {subscription_type} в {time_str} не найдена.")
            return

        user_id = callback_query.from_user.id
        hour, minute = time_obj.hour, time_obj.minute

        possible_job_ids = [
            f"report_{user_id}_{subscription_type}_daily_{hour}_{minute}",
            f"report_{user_id}_{subscription_type}_weekly_{hour}_{minute}",
            f"report_{user_id}_{subscription_type}_monthly_{hour}_{minute}"
        ]

        removed_jobs = 0
        for job_id in possible_job_ids:
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
                logging.info(f"Удалена задача планировщика: {job_id}")
                removed_jobs += 1

        if removed_jobs == 0:
            logging.warning(f"Не найдено задач для удаления по подписке {subscription_type} в {time_str}")
        else:
            logging.info(f"Удалено {removed_jobs} задач из планировщика")

        # 👇 добавляем кнопку "Вернуться в главное меню"
        await callback_query.message.answer(
            text=f"✅ Вы успешно отменили подписку на <b>{subscription_type}</b> в <b>{time_str}</b>.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logging.error(f"Ошибка при удалении подписки: {e}", exc_info=True)
        await callback_query.message.answer("Произошла ошибка при удалении подписки. Попробуйте позже.")
    finally:
        await conn.close()



@save_time_router.callback_query(F.data.startswith("subscription_"))
async def manage_subscription(callback_query: CallbackQuery):
    subscription_data = callback_query.data.split("_")
    subscription_type = subscription_data[1]
    time = subscription_data[2]

    await callback_query.message.answer(f"Вы выбрали подписку: {subscription_type} - Время: {time}.")

    buttons = [
        [InlineKeyboardButton(text="Удалить подписку ❌", callback_data=f"unsubscribe_{subscription_type}_{time}")],
        [InlineKeyboardButton(text="Назад ↩️", callback_data="back_to_subscriptions")]

    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback_query.message.answer("Что вы хотите сделать с этой подпиской?", reply_markup=keyboard)


@save_time_router.callback_query(F.data == "back_to_subscriptions")
async def back_to_subscriptions(callback_query: CallbackQuery):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        subscriptions = await conn.fetch(''' 
            SELECT subscription_type, periodicity, weekday, day_of_month, time, report_type
            FROM subscriptions
            WHERE user_id = $1
        ''', callback_query.from_user.id)

        if not subscriptions:
            await callback_query.message.answer(
                "Вы не подписаны ни на одну рассылку.",
                reply_markup=get_main_menu_keyboard()
            )
            return

        subscriptions_text = "📋 Ваши текущие подписки:\n\n"
        buttons = []
        weekday_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

        for sub in subscriptions:
            report_type = all_types.get(sub['report_type'], f"❓ {sub['report_type']}")
            period = all_time_periods.get(sub['periodicity'], sub['periodicity'])

            subscription_text = f"• {report_type}, {period}"

            if sub['weekday'] is not None:
                subscription_text += f", {weekday_names[sub['weekday']]}"

            if sub['day_of_month'] is not None:
                subscription_text += f", {sub['day_of_month']} число"

            subscription_text += f", {sub['time']}"

            buttons.append([InlineKeyboardButton(
                text=f"📌 {report_type} ({period})",
                callback_data=f"subscription_{sub['subscription_type']}_{sub['time']}"
            )])

            subscriptions_text += f"{subscription_text}\n"

        # Добавляем кнопки навигации
        buttons.append([
            InlineKeyboardButton(text="↩️ Назад", callback_data="show_subscriptions"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback_query.message.answer(subscriptions_text, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Error fetching subscriptions: {e}")
        await callback_query.message.answer(
            "Произошла ошибка при извлечении подписок. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        await conn.close()


@save_time_router.callback_query(F.data.startswith("tz_"))
async def choose_timezone(callback_query: CallbackQuery, state: FSMContext):
    timezone_offset = int(callback_query.data.split("_")[1])
    await state.update_data(timezone_offset=timezone_offset)

    data = await state.get_data()
    sub_type = data.get("sub_type")

    if sub_type == "weekly":

        await state.set_state(SubscriptionState.choosing_day)
        days_kb = weekdays_kb
        await callback_query.message.answer("Выберите день недели:", reply_markup=days_kb)
    elif sub_type == "monthly":

        await state.set_state(SubscriptionState.choosing_monthly_day)
        await callback_query.message.answer("Введите число месяца (от 1 до 31), в которое хотите получать рассылку.")
    else:

        await state.set_state(SubscriptionState.choosing_time)
        logging.info(f"Установлено состояние: SubscriptionState.choosing_time")
        await callback_query.message.answer("Теперь введите время рассылки в формате HH:MM.")


async def save_subscription(
        conn,
        user_id: int,
        subscription_type: str,
        periodicity: str,
        time: datetime.time,
        timezone_offset: int,
        report_type: str,
        state: FSMContext,  # Добавляем state в параметры
        weekday: Optional[int] = None,
        day_of_month: Optional[int] = None,
        date_periodity: Optional[str] = None,
        department: Optional[str] = None
) -> None:
    """Получаем menu_buttons непосредственно из состояния"""

    # Получаем текущие выборы из состояния
    state_data = await state.get_data()
    menu_buttons = state_data.get("menu_selections", {}).get("selected_buttons", [])

    # Преобразуем в строку для БД
    buttons_str = ",".join(menu_buttons) if menu_buttons else None

    logging.info(
        f"Сохранение подписки для {user_id}\n"
        f"Выбранные разделы: {buttons_str or 'Нет'}"
    )

    try:
        existing = await conn.fetchrow(
            """SELECT id FROM subscriptions 
            WHERE user_id = $1 AND report_type = $2 AND department = $3""",
            user_id, report_type, department
        )

        if existing:
            await conn.execute(
                """UPDATE subscriptions SET
                    menu_buttons = $4,
                    subscription_type = $5,
                    periodicity = $6,
                    time = $7,
                    timezone_offset = $8,
                    is_active = TRUE,
                    updated_at = NOW()
                WHERE id = $9""",
                buttons_str,
                subscription_type,
                periodicity,
                time,
                timezone_offset,
                existing['id']
            )
        else:
            await conn.execute(
                """INSERT INTO subscriptions 
                (user_id, subscription_type, periodicity, time, 
                 timezone_offset, report_type, department, menu_buttons)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                user_id,
                subscription_type,
                periodicity,
                time,
                timezone_offset,
                report_type,
                department,
                buttons_str
            )
    except Exception as e:
        logging.error(f"Ошибка сохранения: {e}\nДанные: {buttons_str}")
        raise


@save_time_router.message(SubscriptionState.choosing_time)
async def handle_subscription_time(message: Message, state: FSMContext):
    time_str = message.text.strip()

    try:
        # Проверка формата времени
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', time_str):
            raise ValueError("Неверный формат времени. Используйте ЧЧ:ММ (например, 09:30 или 13:45)")

        time_obj = datetime.strptime(time_str, '%H:%M').time()
        data = await state.get_data()

        # Логирование данных состояния
        logging.info(f"Данные состояния: {data}")

        report_type = data.get("report:type")
        period_key = data.get("report:period")
        sub_type = data.get("sub_type")
        timezone_offset = int(data.get("timezone_offset", 0))

        all_departments_flag = data.get("report_all_departments", False)
        single_department = data.get("report:department")

        # Получаем русские названия из словарей
        report_type_name = all_types.get(report_type, report_type)
        period_name = all_periods.get(period_key, period_key)
        sub_type_name = {
            "daily": "Ежедневно",
            "weekly": "Еженедельно",
            "monthly": "Ежемесячно",
            "workdays": "По рабочим дням"
        }.get(sub_type, sub_type)

        # Получаем название подразделения по токену
        department_name = single_department
        try:
            departments = await all_departments(message.from_user.id)
            if departments and isinstance(departments, dict):
                department_name = departments.get(single_department, single_department)
        except Exception as e:
            logging.error(f"Ошибка получения названия подразделения: {e}")

        if not report_type:
            await message.answer("❌ Ошибка: не выбран тип отчета", reply_markup=get_main_menu_keyboard())
            return
        if not period_key:
            await message.answer("❌ Ошибка: не выбран период отчета", reply_markup=get_main_menu_keyboard())
            return

        conn = await asyncpg.connect(**DB_CONFIG)
        success_count = 0

        try:
            # Обработка подразделений
            departments_to_process = []
            if all_departments_flag:
                departments_to_process = [""]
            elif single_department:
                departments_to_process = [single_department]
            else:
                await message.answer("❌ Ошибка: подразделение не выбрано", reply_markup=get_main_menu_keyboard())
                return

            # Сохранение подписок
            for dep_id in departments_to_process:
                try:
                    await conn.execute(
                        """
                        INSERT INTO subscriptions 
                        (user_id, subscription_type, periodicity, time, timezone_offset, 
                         report_type, weekday, day_of_month, date_periodity, department, menu_buttons)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        """,
                        int(message.from_user.id),
                        str(sub_type),
                        str(sub_type),
                        time_obj,
                        int(timezone_offset),
                        str(report_type),
                        int(data.get("weekday")) if data.get("weekday") is not None else None,
                        int(data.get("day_of_month")) if data.get("day_of_month") is not None else None,
                        str(period_key),
                        str(dep_id),
                        str(data.get("report:format_type", "")))

                    await add_subscription_task(
                        bot=message.bot,
                        user_id=message.from_user.id,
                        sub_type=sub_type,
                        periodicity=sub_type,
                        weekday=data.get("weekday"),
                        day_of_month=data.get("day_of_month"),
                        time_obj=time_obj,
                        date_periodity=period_key,
                        report_type=report_type,
                        department=dep_id,
                        menu_buttons=data.get("report:format_type", ""))

                    success_count += 1
                except Exception as e:
                    logging.error(f"Ошибка подписки для {dep_id}: {e}")
                    await message.answer(f"❌ Ошибка для подразделения {dep_id}", reply_markup=get_main_menu_keyboard())

            # Формирование ответа
            menu_buttons = data.get("report:format_type", "")
            translated_buttons = []
            if menu_buttons:
                button_keys = (
                    menu_buttons if isinstance(menu_buttons, list)
                    else menu_buttons.split(",")
                )

                for btn in button_keys:
                    btn_clean = btn.strip()
                    translated = menu_button_translations.get(btn_clean)
                    if translated and translated not in translated_buttons:
                        translated_buttons.append(translated)
                    else:
                        logging.warning(f"Неизвестная форма отчёта: {btn_clean}")

            if all_departments_flag:
                header = (
                    f"✅ <b>Подписка оформлена</b>\n\n"
                    f"🏢 <b>Подразделения:</b> Все сети\n"
                    f"⏰ <b>Время отправки:</b> {time_str}\n"
                    f"📋 <b>Тип отчета:</b> {report_type_name}\n"
                    f"🗓 <b>Период:</b> {period_name}\n"
                    f"📅 <b>Периодичность:</b> {sub_type_name}"
                )
            else:
                header = (
                    f"✅ <b>Подписка оформлена</b>\n\n"
                    f"🏢 <b>Подразделение:</b> {department_name}\n"
                    f"⏰ <b>Время отправки:</b> {time_str}\n"
                    f"📋 <b>Тип отчета:</b> {report_type_name}\n"
                    f"🗓 <b>Период:</b> {period_name}\n"
                    f"📅 <b>Периодичность:</b> {sub_type_name}"
                )

            if data.get("weekday"):
                weekday_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
                header += f"\n📆 <b>День недели:</b> {weekday_names[data['weekday']]}"
            elif data.get("day_of_month"):
                header += f"\n📆 <b>День месяца:</b> {data['day_of_month']}"

            if translated_buttons:
                header += f"\n\n📌 <b>Форма отчёта:</b>\n" + "\n".join(translated_buttons)

            await message.answer(header, parse_mode="HTML", reply_markup=get_main_menu_keyboard())

        except Exception as e:
            logging.error(f"Ошибка сохранения: {e}")
            await message.answer("❌ Ошибка оформления подписки", reply_markup=get_main_menu_keyboard())
        finally:
            await conn.close()

        if success_count > 0:
            await state.clear()

    except ValueError as e:
        await message.answer(f"❌ {str(e)}", reply_markup=get_main_menu_keyboard())
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer("❌ Произошла ошибка", reply_markup=get_main_menu_keyboard())


async def send_report_task(bot, user_id, report_type, department):
    try:
        logging.info(f"Отправка отчёта пользователю {user_id} для отчёта типа {report_type}, подразделение: {department}")
        # Пример отправки отчёта (это должно быть заменено на вашу логику)
        state_data = {
            "report:type": report_type,
            "report:department": department
        }
        texts = await generate_report(tgid=user_id, state_data=state_data)
        caption = f"Ваш отчёт ({report_type}) за период: {state_data['report:period']}\nПодразделение: {department}\n\n"

        for text in texts:
            parse_mode = "Markdown" if "**" in text else "HTML"
            await bot.send_message(user_id, caption + text, parse_mode=parse_mode)

        logging.info(f"Отчёт {report_type} успешно отправлен пользователю {user_id}.")
    except Exception as e:
        logging.error(f"Ошибка при отправке отчёта пользователю {user_id}: {e}")
        await bot.send_message(user_id, "Произошла ошибка при отправке отчёта. Попробуйте позже.")


async def save_subscription_for_department(
        department: str,
        msg_data: MsgData,
        conn: asyncpg.Connection,
        menu_buttons: Optional[str] = None
) -> None:
    """Сохраняет подписку для конкретного подразделения с учетом выбранных кнопок меню"""
    try:
        # Получаем данные из состояния
        state_data = await msg_data.state.get_data()

        await save_subscription(
            conn=conn,
            user_id=msg_data.tgid,
            subscription_type=state_data.get("sub_type", "scheduled"),
            periodicity=state_data.get("sub_type", "daily"),
            time=state_data.get("report:time"),
            timezone_offset=state_data.get("timezone_offset", 0),
            report_type=state_data.get("report:type"),
            weekday=state_data.get("weekday"),
            day_of_month=state_data.get("day_of_month"),
            date_periodity=state_data.get("report:period"),
            department=department,
            menu_buttons=menu_buttons or state_data.get("menu_buttons")
        )
        logging.info(f"Подписка сохранена для подразделения {department}")

    except Exception as e:
        logging.error(f"Ошибка сохранения подписки для подразделения {department}: {e}")
        raise


async def save_all_subscriptions(msg_data: MsgData):
    # Создаем соединение с базой данных
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        state_data = await msg_data.state.get_data()
        departments = await all_departments(msg_data.tgid)

        for dep in departments:
            await save_subscription_for_department(dep, msg_data, conn)

        logging.info("Подписки для всех подразделений сохранены.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении подписок: {e}")
    finally:
        await conn.close()  # Закрываем соединение


async def finish_selection(msg_data: MsgData) -> None:
    state_data = await msg_data.state.get_data()

    departments = await all_departments(msg_data.tgid)

    # Создайте соединение с базой данных
    conn = await asyncpg.connect(**DB_CONFIG)

    if state_data.get("report_all_departments"):
        await save_all_subscriptions(msg_data)
        text = "Подписки для всех подразделений сохранены."
    else:
        department_id = state_data.get("report_department")
        selected_department = next(dep for dep in departments if dep['id'] == department_id)
        await save_subscription_for_department(selected_department, msg_data, conn)
        text = f"Подписка для подразделения {selected_department['name']} сохранена."

    await msg_data.msg.edit_text(text=text)
    await conn.close()  # Закрытие соединения


@save_time_router.message(SubscriptionState.choosing_time)
async def handle_mailing_time(message: Message, state: FSMContext):
    time_str = message.text.strip()

    try:
        # Валидация времени
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', time_str):
            raise ValueError("Используйте формат ЧЧ:ММ (например, 09:30)")

        time_obj = datetime.strptime(time_str, '%H:%M').time()
        state_data = await state.get_data()

        # Проверяем выбор разделов
        if not state_data.get("menu_selections", {}).get("selected_buttons"):
            await message.answer("❌ Вы не выбрали ни одного раздела отчета")
            return

        # Сохраняем подписку
        async with asyncpg.create_pool(**DB_CONFIG) as pool:
            async with pool.acquire() as conn:
                await save_subscription(
                    conn=conn,
                    user_id=message.from_user.id,
                    subscription_type="scheduled",
                    periodicity=state_data.get("periodicity", "daily"),
                    time=time_obj,
                    timezone_offset=state_data.get("timezone_offset", 0),
                    report_type=state_data["report:type"],
                    department=state_data["report:department"],
                    state=state  # Передаем состояние
                )

        # Формируем отчет о подписке
        selected_buttons = state_data["menu_selections"]["selected_buttons"]
        button_names = {
            "report:show_parameters": "Показатели",
            "report:show_analysis": "Анализ",
            "report:show_negative": "Внимание",
            "report:show_recommendations": "Рекомендации"
        }

        response = [
            "✅ Подписка оформлена",
            f"⏰ Время: {time_str}",
            "📋 Разделы: " + ", ".join([button_names.get(b, b) for b in selected_buttons])
        ]

        await message.answer("\n".join(response))
        await state.clear()

    except ValueError as e:
        await message.answer(f"❌ {str(e)}")
    except Exception as e:
        logging.error(f"Ошибка подписки: {str(e)}")
        await message.answer("❌ Ошибка оформления подписки")


@save_time_router.callback_query(F.data == "report:subscribe_to_mailing")
async def start_subscription_flow(callback: CallbackQuery, state: FSMContext):
    """Единственный обработчик для начала подписки"""
    state_data = await state.get_data()

    required_fields = {
        "report:type": "Тип отчета",
        "report:department": "Подразделение",
        "report:period": "Период данных"
    }

    missing_fields = [name for field, name in required_fields.items() if field not in state_data]
    if missing_fields:
        await callback.answer(f"❌ Сначала выберите: {', '.join(missing_fields)}", show_alert=True)
        return

    # Запускаем процесс выбора типа подписки
    await callback.message.answer(
        "📅 Выберите периодичность рассылки:",
        reply_markup=get_subscription_type_keyboard()
    )
    await state.set_state(SubscriptionState.choosing_period)
    await callback.answer()


def get_subscription_type_keyboard():
    """Клавиатура для выбора типа подписки"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Ежедневно", callback_data="sub_daily"),
            InlineKeyboardButton(text="По рабочим дням", callback_data="sub_workdays")
        ],
        [
            InlineKeyboardButton(text="Еженедельно", callback_data="sub_weekly"),
            InlineKeyboardButton(text="Ежемесячно", callback_data="sub_monthly")
        ]
    ])


@save_time_router.callback_query(F.data.startswith("sub_"), SubscriptionState.choosing_period)
async def process_subscription_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа подписки"""
    sub_type = callback.data.split("_")[1]
    await state.update_data(sub_type=sub_type)

    # Для еженедельной - запрашиваем день недели
    if sub_type == "weekly":
        await callback.message.answer(
            "📆 Выберите день недели для рассылки:",
            reply_markup=weekdays_kb
        )
        await state.set_state(SubscriptionState.choosing_day)

    # Для ежемесячной - запрашиваем день месяца
    elif sub_type == "monthly":
        await callback.message.answer(
            "📆 Введите число месяца (от 1 до 31) для рассылки:"
        )
        await state.set_state(SubscriptionState.choosing_monthly_day)

    # Для остальных - сразу запрашиваем время
    else:
        await callback.message.answer(
            "🌍 Выберите ваш часовой пояс:",
            reply_markup=timezone_kb
        )
        await state.set_state(SubscriptionState.choosing_timezone)

    await callback.answer()


@save_time_router.callback_query(F.data.startswith("day_"), SubscriptionState.choosing_day)
async def process_weekday_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора дня недели"""
    weekday = int(callback.data.split("_")[1])
    await state.update_data(weekday=weekday)

    await callback.message.answer(
        "🌍 Выберите ваш часовой пояс:",
        reply_markup=timezone_kb
    )
    await state.set_state(SubscriptionState.choosing_timezone)
    await callback.answer()


@save_time_router.message(SubscriptionState.choosing_monthly_day)
async def process_monthly_day_selection(message: Message, state: FSMContext):
    """Обработка ввода дня месяца"""
    try:
        day = int(message.text.strip())
        if day < 1 or day > 31:
            raise ValueError

        await state.update_data(day_of_month=day)
        await message.answer(
            "🌍 Выберите ваш часовой пояс:",
            reply_markup=timezone_kb
        )
        await state.set_state(SubscriptionState.choosing_timezone)

    except ValueError:
        await message.answer("❌ Пожалуйста, введите число от 1 до 31")


@save_time_router.message(SubscriptionState.choosing_time)
async def process_time_selection(message: Message, state: FSMContext):
    """Финальный шаг - обработка времени рассылки"""
    try:
        # Валидация времени
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', message.text):
            raise ValueError("Неверный формат времени. Используйте ЧЧ:ММ (например, 09:30)")

        time_obj = datetime.strptime(message.text, '%H:%M').time()
        state_data = await state.get_data()

        # Сохраняем подписку
        async with asyncpg.create_pool(**DB_CONFIG) as pool:
            async with pool.acquire() as conn:
                await save_subscription(
                    conn=conn,
                    user_id=message.from_user.id,
                    subscription_type="scheduled",
                    periodicity=state_data["sub_type"],
                    time=time_obj,
                    timezone_offset=state_data["timezone_offset"],
                    report_type=state_data["report:type"],
                    weekday=state_data.get("weekday"),
                    day_of_month=state_data.get("day_of_month"),
                    date_periodity=state_data["report:period"],
                    department=state_data["report:department"],
                    menu_buttons=get_selected_buttons(state_data)
                )

        # Формируем отчет о подписке
        await send_subscription_confirmation(message, state_data, message.text)
        await state.clear()

    except ValueError as e:
        await message.answer(f"❌ {str(e)}")
    except Exception as e:
        logging.error(f"Subscription error: {e}")
        await message.answer("❌ Произошла ошибка при оформлении подписки")


def get_selected_buttons(state_data: dict) -> Optional[str]:
    """Получаем строку с выбранными кнопками из report:format_type"""
    if "report:format_type" not in state_data:
        logging.warning("⚠️ report:format_type отсутствует в state_data!")
        return None

    buttons = state_data["report:format_type"]
    if isinstance(buttons, list):
        return ",".join(buttons)  # Преобразуем список в строку
    return buttons  # Если уже строка, просто возвращаем


async def send_subscription_confirmation(message: Message, state_data: dict, time_str: str):
    """Отправляем подтверждение подписки"""
    departments = await all_departments(message.from_user.id)
    department_name = departments.get(state_data["report:department"])

    response = [
        f"✅ <b>Подписка оформлена</b>",
        f"",
        f"🏢 <b>Подразделение:</b> {department_name}",
        f"⏰ <b>Время отправки:</b> {time_str}",
        f"📋 <b>Тип отчета:</b> {all_types.get(state_data['report:type'])}",
        f"🗓 <b>Период:</b> {all_periods.get(state_data['report:period'])}",
        f"📅 <b>Периодичность:</b> {get_sub_type_name(state_data['sub_type'])}"
    ]

    if state_data.get("weekday"):
        response.append(f"📆 <b>День недели:</b> {get_weekday_name(state_data['weekday'])}")
    elif state_data.get("day_of_month"):
        response.append(f"📆 <b>День месяца:</b> {state_data['day_of_month']}")

    if buttons := get_selected_buttons(state_data):
        selected = [btn.text.split()[0] for btn in all_menu_buttons if btn.callback_data in buttons.split(',')]
        response.append(f"")
        response.append(f"📌 <b>Выбранные разделы:</b> {', '.join(selected)}")

    await message.answer("\n".join(response), parse_mode="HTML")


def get_sub_type_name(sub_type: str) -> str:
    """Название типа подписки"""
    return {
        "daily": "Ежедневно",
        "workdays": "По рабочим дням",
        "weekly": "Еженедельно",
        "monthly": "Ежемесячно"
    }.get(sub_type, sub_type)

def get_weekday_name(weekday: int) -> str:
    """Название дня недели"""
    return [
        "Понедельник", "Вторник", "Среда",
        "Четверг", "Пятница", "Суббота", "Воскресенье"
    ][weekday]


button_translations = {
    "report:show_parameters": "Показатели 📊",
    "report:show_analysis": "Анализ 🔎",
    "report:show_negative": "Обратите внимание 👀",
    "report:show_negative_analysis": "Обратите внимание 👀 (Анализ)",
    "report:show_recommendations": "Рекомендации 💡",
    "register_mailing": "Подписаться на рассылку 📥"
}

# Функция для перевода кнопок
def translate_button(callback_data):
    return button_translations.get(callback_data, callback_data)
