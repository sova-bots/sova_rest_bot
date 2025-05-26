import logging
import re

from aiogram import Dispatcher, Router, F, types

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
import asyncpg
from datetime import datetime, time

import config as cf

from src.mailing.notifications.keyboards import periodicity_kb, timezone_kb, weekdays_kb
from src.mailing.notifications.select_report import subscribe_notifications, setup_routers_select_reports
from src.sound_and_text_ai.ai_answers import ai_answer


subcsribe_mailing_router = Router()


# Класс состояний для FSM
class MailingStates(StatesGroup):
    waiting_for_time = State()


class Form(StatesGroup):
    choosing_time = State()


class TimeInputState(StatesGroup):
    waiting_for_offset = State()
    waiting_for_time = State()


class SubscriptionState(StatesGroup):
    choosing_frequency = State()
    choosing_type = State()
    choosing_day = State()
    choosing_timezone = State()
    choosing_monthly_day = State()
    choosing_time = State()


DB_CONFIG = cf.DB_CONFIG

logging.basicConfig(level=logging.INFO)


async def init_db_pool():
    db_link = cf.DB_LINK
    return await asyncpg.create_pool(db_link)


db_pool = None


class NotificationGoogleSheetsWorker:
    def __init__(self):
        self.subscribed_ids = []

    def contains_id(self, user_id: int) -> bool:
        """Проверка наличия ID в списке подписок"""
        return user_id in self.subscribed_ids

    def add_id(self, user_id: int) -> None:
        """Добавление ID пользователя в список подписок"""
        if user_id not in self.subscribed_ids:
            self.subscribed_ids.append(user_id)
            logging.info(f"User {user_id} added to subscription list.")

    def remove_id(self, user_id: int) -> None:
        """Удаление ID пользователя из списка подписок"""
        if user_id in self.subscribed_ids:
            self.subscribed_ids.remove(user_id)
            logging.info(f"User {user_id} removed from subscription list.")


@subcsribe_mailing_router.callback_query(F.data == 'register_mailing')
async def subscribe_to_mailing(callback_query: CallbackQuery, state: FSMContext):
    logging.info(f"User {callback_query.from_user.id} started subscription process.")
    keyboard = periodicity_kb
    await callback_query.message.answer("Выберите периодичность рассылки:", reply_markup=keyboard)


@subcsribe_mailing_router.callback_query(F.data.startswith("sub_"))
async def choose_subscription_type(callback_query: CallbackQuery, state: FSMContext):
    sub_type = callback_query.data.split("_")[1]
    logging.info(f"User {callback_query.from_user.id} selected subscription type: {sub_type}")

    await state.update_data(sub_type=sub_type)

    if sub_type == "daily":
        await state.update_data(frequency="Ежедневно")
    elif sub_type == "workdays":
        await state.update_data(frequency="По будням (Пн-Пт)")
    elif sub_type == "weekly":
        await state.update_data(frequency="Еженедельно")
    elif sub_type == "monthly":
        await state.update_data(frequency="Ежемесячно")

    await state.set_state(SubscriptionState.choosing_timezone)
    logging.info(f"User {callback_query.from_user.id} moved to state: choosing_timezone")
    await callback_query.message.answer("Выберите ваш часовой пояс:", reply_markup=timezone_kb)


@subcsribe_mailing_router.callback_query(F.data.startswith("tz_"))
async def choose_timezone(callback_query: CallbackQuery, state: FSMContext):
    timezone_offset = int(callback_query.data.split("_")[1])
    logging.info(f"User {callback_query.from_user.id} selected timezone offset: {timezone_offset}")
    await state.update_data(timezone_offset=timezone_offset)

    data = await state.get_data()
    logging.info(f"State data: {data}")

    sub_type = data.get("sub_type")

    if sub_type == "weekly":
        await state.set_state(SubscriptionState.choosing_day)
        logging.info(f"User {callback_query.from_user.id} moved to state: choosing_day")
        days_kb = weekdays_kb
        await callback_query.message.answer("Выберите день недели:", reply_markup=days_kb)
    elif sub_type == "monthly":
        await state.set_state(SubscriptionState.choosing_monthly_day)
        logging.info(f"User {callback_query.from_user.id} moved to state: choosing_monthly_day")
        await callback_query.message.answer("Введите число месяца (от 1 до 31), в которое хотите получать рассылку.")
    else:
        await state.set_state(SubscriptionState.choosing_time)
        logging.info(f"User {callback_query.from_user.id} moved to state: choosing_time")
        await callback_query.message.answer("Теперь введите время рассылки в формате ЧЧ:ММ.")


@subcsribe_mailing_router.message(SubscriptionState.choosing_day)
async def choose_weekday_or_day(message: Message, state: FSMContext):
    try:
        value = int(message.text)
        data = await state.get_data()
        logging.info(f"Received data: {data}")

        if "weekly" in data:  # Если выбрана еженедельная подписка
            if value < 0 or value > 6:
                raise ValueError("В неделе только дни с 0 (понедельник) до 6 (воскресенье).")
            await state.update_data(weekday=value)
            logging.info(f"Updated data with weekday={value}. State: {await state.get_data()}")
            await message.answer("Теперь выберите время рассылки в формате ЧЧ:ММ.")
            await state.set_state(SubscriptionState.choosing_time)
            logging.info("State set to SubscriptionState.choosing_time")
        elif "monthly" in data:  # Если выбрана ежемесячная подписка
            if value < 1 or value > 31:
                raise ValueError("В месяце только числа с 1 по 31.")
            await state.update_data(day_of_month=value)
            logging.info(f"Updated data with day_of_month={value}. State: {await state.get_data()}")
            await message.answer("Теперь выберите время рассылки в формате ЧЧ:ММ.")
            await state.set_state(SubscriptionState.choosing_time)
            logging.info("State set to SubscriptionState.choosing_time")
    except ValueError as e:
        await message.answer(str(e))


@subcsribe_mailing_router.message(SubscriptionState.choosing_monthly_day)
async def choose_day_of_month(message: Message, state: FSMContext):
    try:
        day = int(message.text.strip())
        logging.info(f"User {message.from_user.id} is trying to set day: {day}")

        if 1 <= day <= 31:
            await state.update_data(day_of_month=day)
            await state.set_state(SubscriptionState.choosing_time)
            logging.info(f"User {message.from_user.id} successfully set day of month to {day}.")
            await message.answer("Теперь введите время рассылки в формате ЧЧ:ММ.")
        else:
            logging.warning(f"User {message.from_user.id} entered invalid day value: {message.text}")
            await message.answer("Введите корректное число от 1 до 31.")
    except ValueError:
        logging.error(f"User {message.from_user.id} entered invalid day value: {message.text}")
        await message.answer("Введите число месяца цифрами (например, 15).")


async def save_time(message: Message, state: FSMContext):
    time_str = message.text.strip()
    try:
        hour, minute = map(int, time_str.split(":"))
        input_time = time(hour, minute)

        data = await state.get_data()
        timezone_offset = data.get("timezone_offset", 0)  # По умолчанию UTC+0

        adjusted_hour = (hour - timezone_offset) % 24  # Вычитаем или добавляем часовой пояс
        adjusted_time = time(adjusted_hour, minute)

        sub_type = data.get("sub_type")
        frequency = data.get("frequency")
        weekday = data.get("weekday", None)
        day_of_month = data.get("day_of_month", None)

        logging.info(f"Adjusted time: {adjusted_time}")

        await save_subscription(
            message.from_user.id, sub_type=sub_type,
            periodicity=frequency,
            weekday=weekday,
            day_of_month=day_of_month,
            time_obj=adjusted_time,
            timezone_offset=timezone_offset
        )

        await message.answer(f"Вы подписались на {frequency}. Время рассылки (ваше локальное): {time_str}.")
        await state.clear()

    except ValueError:
        await message.answer("Неверный формат времени. Пожалуйста, используйте формат ЧЧ:ММ.")


@subcsribe_mailing_router.callback_query(F.data == 'show_subscriptions')
async def show_subscriptions(callback_query: CallbackQuery):
    logging.info(f"User {callback_query.from_user.id} requested to show subscriptions.")
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        subscriptions = await conn.fetch(''' 
            SELECT subscription_type, periodicity, weekday, day_of_month, time
            FROM subscriptions
            WHERE user_id = $1
        ''', callback_query.from_user.id)

        if not subscriptions:
            logging.info(f"User {callback_query.from_user.id} has no subscriptions.")
            await callback_query.message.answer("Вы не подписаны ни на одну рассылку.")
            return

        logging.info(f"Found {len(subscriptions)} subscriptions for user {callback_query.from_user.id}.")
        buttons = []
        for sub in subscriptions:
            subscription_text = f"{sub['subscription_type']} ({sub['periodicity']})"
            if sub['weekday'] is not None:
                weekday_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
                subscription_text += f" - {weekday_names[sub['weekday']]}"
            if sub['day_of_month'] is not None:
                subscription_text += f" - {sub['day_of_month']} число месяца"
            subscription_text += f" - Время: {sub['time']}"

            buttons.append([types.InlineKeyboardButton(text=subscription_text,
                                                       callback_data=f"subscription_{sub['subscription_type']}_{sub['time']}")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback_query.message.answer("Ваши подписки:", reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Error fetching subscriptions for user {callback_query.from_user.id}: {e}")
        await callback_query.message.answer("Произошла ошибка при извлечении подписок. Попробуйте позже.")
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


@subcsribe_mailing_router.callback_query(F.data.startswith("unsubscribe_"))
async def unsubscribe(callback_query: CallbackQuery):
    subscription_data = callback_query.data.split("_")

    if len(subscription_data) < 3:
        await callback_query.message.answer("Невозможно получить данные для отмены подписки.")
        return

    subscription_type = subscription_data[1]
    time_str = subscription_data[2]

    print(f"Полученные данные: subscription_type={subscription_type}, time_str={time_str}")

    if len(time_str) > 5:
        time_str = time_str[:5]

    try:
        time_obj = datetime.strptime(time_str, '%H:%M').time()  # Используем формат без секунд
    except ValueError:
        await callback_query.message.answer(f"Некорректное время для подписки: {time_str}. Ожидаемый формат - ЧЧ:ММ.")
        return

    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        await conn.execute(''' 
            DELETE FROM subscriptions 
            WHERE user_id = $1 AND subscription_type = $2 AND time = $3
        ''', callback_query.from_user.id, subscription_type, time_obj)

        await callback_query.message.answer(f"Вы успешно отменили подписку на {subscription_type} в {time_str}.")
    except Exception as e:
        logging.error(f"Ошибка при удалении подписки: {e}")
        await callback_query.message.answer("Произошла ошибка при удалении подписки. Попробуйте позже.")
    finally:
        await conn.close()


# Обработчик нажатия на кнопку подписки
@subcsribe_mailing_router.callback_query(F.data.startswith("subscription_"))
async def manage_subscription(callback_query: CallbackQuery):
    subscription_data = callback_query.data.split("_")
    subscription_type = subscription_data[1]
    time = subscription_data[2]

    await callback_query.message.answer(f"Вы выбрали подписку: {subscription_type} - Время: {time}.")

    buttons = [
        [InlineKeyboardButton(text="Удалить подписку ❌", callback_data=f"unsubscribe_{subscription_type}_{time}")],
        [InlineKeyboardButton(text="Назад ↩️", callback_data="back_to_subscriptions")]  # Кнопка назад

    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback_query.message.answer("Что вы хотите сделать с этой подпиской?", reply_markup=keyboard)


@subcsribe_mailing_router.callback_query(F.data == "back_to_subscriptions")
async def back_to_subscriptions(callback_query: CallbackQuery):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        subscriptions = await conn.fetch(''' 
            SELECT subscription_type, periodicity, weekday, day_of_month, time
            FROM subscriptions
            WHERE user_id = $1
        ''', callback_query.from_user.id)

        if not subscriptions:
            await callback_query.message.answer("Вы не подписаны ни на одну рассылку.")
            return

        subscriptions_text = ""
        buttons = []
        for sub in subscriptions:
            subscription_text = f"{sub['subscription_type']} ({sub['periodicity']})"
            if sub['weekday'] is not None:
                weekday_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
                subscription_text += f" - {weekday_names[sub['weekday']]}"
            if sub['day_of_month'] is not None:
                subscription_text += f" - {sub['day_of_month']} число месяца"
            subscription_text += f" - Время: {sub['time']}"

            buttons.append([InlineKeyboardButton(text=subscription_text,
                                                 callback_data=f"subscription_{sub['subscription_type']}_{sub['time']}")])

            subscriptions_text += f"{subscription_text}\n"

        buttons.append([InlineKeyboardButton(text="Назад к подпискам", callback_data="show_subscriptions")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await callback_query.message.answer(f"Вот ваши подписки:\n{subscriptions_text}", reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Error fetching subscriptions: {e}")
        await callback_query.message.answer("Произошла ошибка при извлечении подписок. Попробуйте позже.")
    finally:
        await conn.close()


@subcsribe_mailing_router.callback_query(F.data.startswith("unsubscribe_"))
async def unsubscribe(callback_query: CallbackQuery):
    subscription_data = callback_query.data.split("_")
    subscription_type = subscription_data[1]
    time_str = subscription_data[2]

    try:
        time_obj = datetime.strptime(time_str, '%H:%M').time()  # Используем формат без секунд
    except ValueError:
        await callback_query.message.answer("Некорректное время для подписки.")
        return

    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        await conn.execute(''' 
            DELETE FROM subscriptions 
            WHERE user_id = $1 AND subscription_type = $2 AND time = $3
        ''', callback_query.from_user.id, subscription_type, time_obj)

        await callback_query.message.answer(f"Вы успешно отменили подписку на {subscription_type} в {time_str}.")
    except Exception as e:
        logging.error(f"Failed to unsubscribe: {e}")
        await callback_query.message.answer("Произошла ошибка при удалении подписки. Попробуйте позже.")
    finally:
        await conn.close()


@subcsribe_mailing_router.message(SubscriptionState.choosing_time)
async def process_time(message: Message, state: FSMContext):
    logging.info(f"Processing time input for user {message.from_user.id}")  # Логируем начало обработки
    time_str = message.text.strip()
    logging.info(f"User inputted time: {time_str}")

    if not re.match(r"^\d{2}:\d{2}$", time_str):  # Проверка формата ЧЧ:ММ
        logging.error(f"Invalid time format: {time_str}")
        await message.answer("Неверный формат времени. Пожалуйста, используйте формат ЧЧ:ММ.")
        return

    try:
        hour, minute = map(int, time_str.split(":"))
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError("Некорректное время.")

        input_time = time(hour, minute)

        data = await state.get_data()
        logging.info(f"State data: {data}")  # Логируем данные состояния

        timezone_offset = data.get("timezone_offset", 0)
        adjusted_hour = (hour - timezone_offset) % 24
        adjusted_time = time(adjusted_hour, minute)

        logging.info(f"Adjusted time (with timezone offset): {adjusted_time}")

        sub_type = data.get("sub_type")
        frequency = data.get("frequency")
        weekday = data.get("weekday", None)
        day_of_month = data.get("day_of_month", None)

        logging.info(f"Saving subscription for user {message.from_user.id}:")
        logging.info(f"  - Subscription type: {sub_type}")
        logging.info(f"  - Periodicity: {frequency}")
        logging.info(f"  - Weekday: {weekday}")
        logging.info(f"  - Day of month: {day_of_month}")
        logging.info(f"  - Time: {adjusted_time}")
        logging.info(f"  - Timezone offset: {timezone_offset}")

        await save_subscription(
            message.from_user.id, sub_type=sub_type,
            periodicity=frequency,
            weekday=weekday,
            day_of_month=day_of_month,
            time_obj=adjusted_time,
            timezone_offset=timezone_offset
        )

        await message.answer(f"Вы подписались на {frequency}. Время рассылки (ваше локальное): {time_str}.")
        await state.clear()

    except ValueError as e:
        logging.error(f"Invalid time format entered: {time_str}. Error: {e}")  # Логируем ошибку
        await message.answer("Неверный формат времени. Пожалуйста, используйте формат ЧЧ:ММ.")


async def save_subscription(user_id, sub_type, periodicity, weekday, day_of_month, time_obj, timezone_offset):
    logging.info(f"Saving subscription for user {user_id}:")
    logging.info(f"  - Subscription type: {sub_type}")
    logging.info(f"  - Periodicity: {periodicity}")
    logging.info(f"  - Weekday: {weekday}")
    logging.info(f"  - Day of month: {day_of_month}")
    logging.info(f"  - Time: {time_obj}")
    logging.info(f"  - Timezone offset: {timezone_offset}")

    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        logging.info("Executing SQL query to save subscription.")
        await conn.execute(''' 
        INSERT INTO subscriptions(user_id, subscription_type, periodicity, weekday, day_of_month, time, timezone_offset)
        VALUES($1, $2, $3, $4, $5, $6, $7)
        ''', user_id, sub_type, periodicity, weekday, day_of_month, time_obj, timezone_offset)
        logging.info(f"Сохраняем подписку с периодичностью: {periodicity}")

        logging.info(f"Subscription for user {user_id} saved successfully.")
    except Exception as e:
        logging.error(f"Failed to save subscription: {e}")
    finally:
        await conn.close()
