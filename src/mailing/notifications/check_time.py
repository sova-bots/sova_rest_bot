import logging
import os
from typing import Optional

import pytz
from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, FSInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import asyncpg
from datetime import time
import config as cf

scheduler = AsyncIOScheduler()

class SubscriptionStates(StatesGroup):
    choosing_frequency = State()
    choosing_type = State()
    choosing_day = State()
    choosing_timezone = State()
    choosing_weekday = State()
    choosing_day_of_month = State()
    choosing_monthly_day = State()  # Новый state для выбора дня месяца
    choosing_time = State()
    choosing_report_format = State()

class TimeInputState(StatesGroup):
    waiting_for_offset = State()
    waiting_for_time = State()


class Form(StatesGroup):
    choosing_time = State()


check_time_router = Router()


DB_CONFIG = cf.DB_CONFIG


async def generate_report_file(report_type: str, file_format: str) -> str:
    """Генерирует отчёт и возвращает путь к файлу."""
    try:
        # Определяем базовый путь для отчётов
        base_path = r"C:\WORK\sova_rest_bot\sova_rest_bot-master\src\basic"

        # Формируем путь к файлу в зависимости от типа отчёта и формата
        file_path = os.path.join(base_path, report_type, f"{report_type}.{file_format}")

        if not os.path.exists(file_path):
            logging.error(f"Файл не найден: {file_path}")
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        logging.info(f"Файл {file_path} существует, можно отправлять")
        return file_path

    except Exception as e:
        logging.error(f"Ошибка генерации файла: {e}")
        raise


async def get_subscriptions_from_db():
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        result = await conn.fetch('''
            SELECT user_id, subscription_type, periodicity, weekday, day_of_month, time, timezone_offset, report_type, report_format, token 
            FROM subscriptions 
            WHERE periodicity = 'daily' OR periodicity = 'weekly' OR periodicity = 'monthly';
        ''')
        logging.info(f"Retrieved {len(result)} subscriptions from DB")
        return result
    except Exception as e:
        logging.error(f"Failed to get subscriptions: {e}")
        return []
    finally:
        await conn.close()


async def add_subscription_task(bot: Bot, user_id, sub_type, time_obj, report_type, report_format):
    hour, minute = time_obj.hour, time_obj.minute
    logging.info(f"Adding task for user {user_id} at {hour}:{minute} for {sub_type} report in {report_format} format.")

    scheduler.add_job(
        send_report,
        CronTrigger(hour=hour, minute=minute),
        args=[bot, user_id, report_type, report_format],  # Передаём формат отчёта
        id=f"report_{user_id}_{sub_type}_{hour}_{minute}",
        replace_existing=True
    )


@check_time_router.callback_query(F.data.startswith("format_"), SubscriptionStates.choosing_report_format)
async def choose_report_format(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Обработчик выбора формата отчёта."""
    report_format = callback.data.split("_")[1]  # Получаем формат (pdf или excel)
    await state.update_data(report_format=report_format)  # Сохраняем формат в состоянии
    logging.info(f"Выбран формат отчёта: {report_format}")

    # Получаем все данные из состояния
    data = await state.get_data()
    user_id = callback.from_user.id
    sub_type = data.get("sub_type")
    timezone_offset = data.get("timezone_offset", 0)
    weekday = data.get("weekday", None)
    day_of_month = data.get("day_of_month", None)
    time_obj = data.get("time_obj")
    report_type = data.get("report_type", "revenue_analysis")

    # Сохраняем подписку
    await save_subscription(
        bot=bot,
        user_id=user_id,
        sub_type=sub_type,
        periodicity="daily",  # Пример
        weekday=weekday,
        day_of_month=day_of_month,
        time_obj=time_obj,
        timezone_offset=timezone_offset,
        report_type=report_type,
        report_format=report_format,
        token="dummy_token"
    )

    await callback.message.answer(f"Вы подписались на рассылку. Формат отчёта: {report_format}.")
    await state.clear()  # Очищаем состояние


async def send_report(bot: Bot, user_id: int, report_type: str, report_format: str):
    """Отправляет отчёт пользователю."""
    logging.info(f"Попытка отправить отчёт {report_type} в формате {report_format} пользователю {user_id}")

    try:
        # Генерируем файл отчёта
        file_path = await generate_report_file(report_type, report_format)

        if not os.path.exists(file_path):
            logging.error(f"Файл {file_path} не найден.")
            await bot.send_message(user_id, f"Ошибка: файл отчёта ({file_path}) не найден.")
            return

        # Отправляем файл пользователю
        file = FSInputFile(file_path)
        await bot.send_document(user_id, document=file, caption=f"Ваш отчёт ({report_type}) в формате {report_format}.")
        logging.info(f"Отчёт {report_type} отправлен пользователю {user_id}.")

    except Exception as e:
        logging.error(f"Ошибка при отправке отчёта пользователю {user_id}: {e}")
        await bot.send_message(user_id, "Произошла ошибка при отправке отчёта. Попробуйте позже.")


async def send_handle_format_pdf(bot: Bot, user_id: int):
    logging.info(f"Generating PDF report for user {user_id}")
    file_path = await generate_report_file("revenue_analysis", "pdf")

    if not os.path.exists(file_path):
        logging.error(f"File {file_path} does not exist.")
        return

    try:
        logging.info(f"Sending PDF file {file_path} to user {user_id}")
        file = FSInputFile(file_path)  # Используем FSInputFile
        await bot.send_document(user_id, document=file)
        logging.info(f"PDF report sent to user {user_id}.")
    except Exception as e:
        logging.error(f"Failed to send PDF report to user {user_id}: {e}")

async def send_handle_format_excel(bot: Bot, user_id: int):
    logging.info(f"Generating Excel report for user {user_id}")
    file_path = await generate_report_file("revenue_analysis", "excel")

    if not os.path.exists(file_path):
        logging.error(f"File {file_path} does not exist.")
        return

    try:
        logging.info(f"Sending Excel file {file_path} to user {user_id}")
        file = FSInputFile(file_path)  # Используем FSInputFile
        await bot.send_document(user_id, document=file)
        logging.info(f"Excel report sent to user {user_id}.")
    except Exception as e:
        logging.error(f"Failed to send Excel report to user {user_id}: {e}")


async def schedule_all_subscriptions(bot: Bot):
    """Планирует все подписки из базы данных."""
    subscriptions = await get_subscriptions_from_db()

    for sub in subscriptions:
        user_id = sub['user_id']
        sub_type = sub['subscription_type']
        time_obj = sub['time']
        report_type = sub['report_type']
        report_format = sub.get('report_format', 'pdf')  # Используем значение по умолчанию, если ключ отсутствует

        # Добавляем задачу в планировщик
        await add_subscription_task(bot, user_id, sub_type, time_obj, report_type, report_format)


async def send_notification(bot: Bot, user_id: int, report_type: str, time_obj: time):
    """Отправляет уведомление пользователю."""
    logging.info(f"Отправка уведомления пользователю {user_id}")
    try:
        message = f"Отчёт ({report_type}) запланирован на {time_obj.strftime('%H:%M')}."
        await bot.send_message(user_id, message)
        logging.info(f"Уведомление отправлено пользователю {user_id}")
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")


async def send_message(bot: Bot, user_id: int, report_type: str, file_format: str):
    file_path = await generate_report_file(report_type, file_format)

    # Проверяем, существует ли файл
    if not os.path.exists(file_path):
        logging.error(f"Файл {file_path} не найден!")
        await bot.send_message(user_id, f"Ошибка: файл отчёта ({file_path}) не найден.")
        return

    # Открываем и отправляем
    with open(file_path, "rb") as file:
        await bot.send_document(user_id, FSInputFile(file))


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
    token: str
):
    """Сохраняет подписку в базу данных и добавляет задачу в планировщик."""
    logging.info(f"Сохранение подписки для пользователя {user_id}.")

    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        # Преобразуем timezone_offset в строку для использования с pytz
        timezone_offset_str = f"UTC{('+' if timezone_offset >= 0 else '')}{timezone_offset}:00"
        tz = pytz.timezone(timezone_offset_str)

        # Сохраняем подписку в БД
        await conn.execute(''' 
            INSERT INTO subscriptions(
                user_id, subscription_type, periodicity, weekday, day_of_month, time, timezone_offset, 
                report_type, date_periodity, department, token
            )
            VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        ''', user_id, sub_type, periodicity, weekday, day_of_month, time_obj, timezone_offset,
            report_type, date_periodity, department, token)

        logging.info(f"Подписка для пользователя {user_id} успешно сохранена в базе данных.")

        # Добавляем задачу в планировщик
        await add_subscription_task(
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
            timezone_offset_str=timezone_offset_str
        )

    except Exception as e:
        logging.error(f"Ошибка при сохранении подписки для пользователя {user_id}: {e}")
        raise
    finally:
        await conn.close()


@check_time_router.message(SubscriptionStates.choosing_time)
async def process_time(message: Message, state: FSMContext, bot: Bot):
    """Обработчик ввода времени."""
    time_str = message.text.strip()
    logging.info(f"Пользователь ввёл время: {time_str}")

    try:
        hour, minute = map(int, time_str.split(":"))
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError("Некорректное время.")

        target_time = time(hour, minute)
        user_id = message.from_user.id

        # Получаем данные из состояния
        data = await state.get_data()
        sub_type = data.get("sub_type")
        timezone_offset = data.get("timezone_offset", 0)
        weekday = data.get("weekday", None)
        day_of_month = data.get("day_of_month", None)
        report_type = data.get("report_type", "revenue_analysis")
        report_format = data.get("report_format", "pdf")

        # Сохраняем подписку
        await save_subscription(
            bot=bot,
            user_id=user_id,
            sub_type=sub_type,
            periodicity="daily",  # Пример
            weekday=weekday,
            day_of_month=day_of_month,
            time_obj=target_time,
            timezone_offset=timezone_offset,
            report_type=report_type,
            report_format=report_format,
            token="dummy_token"
        )

        # Отправляем уведомление
        await send_notification(bot, user_id, report_type, target_time)

        await message.answer(f"Отчёт ({report_type}) запланирован на {time_str}.")
        await state.clear()  # Очищаем состояние

    except ValueError as e:
        await message.answer(f"Ошибка: {e}. Пожалуйста, введите время в формате HH:MM.")
    except Exception as e:
        logging.error(f"Ошибка при обработке времени: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")
        await state.clear()  # Очищаем состояние
