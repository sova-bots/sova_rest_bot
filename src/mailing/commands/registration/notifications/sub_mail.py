import logging
from aiogram import Dispatcher, Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import asyncpg
import config as cf
from datetime import datetime

from src.mailing.notifications.keyboards import periodicity_kb, timezone_kb, all_periods, weekdays_kb
from src.analytics.constant.variants import all_departments
from src.mailing.commands.registration.notifications.check_time import generate_report, add_subscription_task

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
    department_id = callback_query.data.split("_")[1]
    await state.update_data(report_department=department_id)
    logging.info(f"Пользователь {callback_query.from_user.id} выбрал подразделение: {department_id}")

    if department_id == "all":
        user_id = callback_query.from_user.id
        all_deps = await all_departments(user_id)
        await state.update_data(report_department=list(all_deps.keys()))
        logging.info(f"Пользователь {user_id} выбрал ВСЕ подразделения: {list(all_deps.keys())}")

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
            await callback_query.message.answer("Вы не подписаны ни на одну рассылку.")
            return

        buttons = []
        for sub in subscriptions:

            subscription_text = f"Тип отчёта: {sub['report_type']}"

            subscription_text += f", Периодичность: {sub['periodicity']}"

            if sub['weekday'] is not None:
                weekday_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
                subscription_text += f", День недели: {weekday_names[sub['weekday']]}"

            if sub['day_of_month'] is not None:
                subscription_text += f", День месяца: {sub['day_of_month']}"

            subscription_text += f", Время: {sub['time']}"

            buttons.append([
                types.InlineKeyboardButton(
                    text=subscription_text,
                    callback_data=f"subscription_{sub['subscription_type']}_{sub['time']}"
                )
            ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback_query.message.answer("Ваши подписки:", reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Ошибка при извлечении подписок: {e}")
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


@save_time_router.callback_query(F.data.startswith("unsubscribe_"))
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

        time_obj = datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        await callback_query.message.answer(f"Некорректное время для подписки: {time_str}. Ожидаемый формат - HH:MM.")
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


@save_time_router.message(SubscriptionState.choosing_time)
async def handle_subscription_time(message: Message, state: FSMContext):
    logging.info("Обработчик времени вызван.")
    time_str = message.text.strip()

    try:
        time_obj = datetime.strptime(time_str, '%H:%M').time()
        data = await state.get_data()

        logging.info(f"Состояние перед обработкой: {data}")

        report_type = data.get("report:type")
        period_key = data.get("report:period")  # Получаем ключ периода (например, "last-day")
        department = data.get("report:department")
        sub_type = data.get("sub_type")
        timezone_offset = data.get("timezone_offset")

        if not report_type:
            logging.error("Не выбран тип отчета.")
            await message.answer("Ошибка: тип отчета не выбран.")
            return
        if not period_key:
            logging.error("Не выбран период отчета.")
            await message.answer("Ошибка: период отчета не выбран.")
            return
        if not department:
            logging.error("Не выбрано подразделение.")
            await message.answer("Ошибка: подразделение не выбрано.")
            return

        conn = await asyncpg.connect(**DB_CONFIG)
        logging.info("Соединение с базой данных установлено.")

        # Сохранение подписки в БД
        await save_subscription(
            conn=conn,
            user_id=message.from_user.id,
            subscription_type=sub_type,
            periodicity=sub_type,
            time=time_obj,
            timezone_offset=timezone_offset,
            report_type=report_type,
            weekday=data.get("weekday"),
            day_of_month=data.get("day_of_month"),
            date_periodity=period_key,  # Передаем ключ периода в базу данных
            department=department
        )

        # Добавление задачи подписки в планировщик
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
            department=department
        )

        await message.answer(f"Вы успешно подписались на рассылку! Время рассылки: {time_str}.")
        await state.clear()
        await conn.close()

    except ValueError:
        logging.error(f"Неверный формат времени: {time_str}")
        await message.answer("Неверный формат времени. Пожалуйста, используйте формат HH:MM.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении подписки: {e}")
        await message.answer("Ошибка при сохранении подписки. Попробуйте позже.")


async def save_subscription(conn, user_id, subscription_type, periodicity, time, timezone_offset,
                            report_type, weekday=None, day_of_month=None, date_periodity=None, department=None):
    try:
        # Приведение timezone_offset к int
        if isinstance(timezone_offset, str):
            timezone_offset = int(timezone_offset)  # Убираем "+" перед числом и приводим к int

        # Добавляем подписку в базу данных
        if isinstance(department, list):
            for dep in department:
                await conn.execute(
                    """
                    INSERT INTO subscriptions (user_id, subscription_type, periodicity, time, timezone_offset, 
                                               report_type, weekday, day_of_month, date_periodity, department)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    user_id, subscription_type, periodicity, time, timezone_offset, report_type, weekday,
                    day_of_month, date_periodity, dep
                )
        else:
            await conn.execute(
                """
                INSERT INTO subscriptions (user_id, subscription_type, periodicity, time, timezone_offset, 
                                           report_type, weekday, day_of_month, date_periodity, department)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                user_id, subscription_type, periodicity, time, timezone_offset, report_type, weekday,
                day_of_month, date_periodity, department
            )

        logging.info(
            f"Подписка сохранена в БД: {user_id}, {subscription_type}, {periodicity}, {time}, {timezone_offset}...")
    except Exception as e:
        logging.error(f"Ошибка при сохранении подписки: {e}")


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
