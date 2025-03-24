import logging
from aiogram import Router, Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import time
import pytz
import asyncpg
from typing import Optional
import config as cf
from src.analytics.api import get_reports
from src.analytics.handlers.text.revenue_texts import revenue_analysis_text
from src.analytics.handlers.text.texts import text_functions
from src.analytics.handlers.types.text_data import TextData

from src.analytics.constant.variants import all_departments

# Инициализация планировщика
scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Moscow"))  # Устанавливаем Московскую временную зону
DB_CONFIG = cf.DB_CONFIG

subscription_router = Router()


async def get_department_name(tgid: int, department_id: str) -> str:
    departments = await all_departments(tgid)
    return departments.get(department_id, department_id)


# Генерация отчёта
async def generate_report(
        tgid: int,
        state_data: dict,
        type_prefix: str = "",
        only_negative: bool = False,
        recommendations: bool = False
) -> list[str]:
    report_type = state_data.get("report:type")
    period = state_data.get("report:period")
    department_uuid = state_data.get("report:department")  # UUID object
    # Convert UUID to string
    department = str(department_uuid) if department_uuid else None

    reports = await get_reports(tgid=tgid, state_data=state_data, type_prefix=type_prefix)

    if None in reports:
        raise ValueError("Не удалось загрузить данные для отчёта.")

    text_func = text_functions[type_prefix + report_type]
    text_data = TextData(reports=reports, period=period, only_negative=only_negative)
    texts: list[str] = text_func(text_data)

    if report_type == "revenue" and recommendations:
        texts = revenue_analysis_text(text_data, msg_type="revenue_recomendations")

    return texts


# Получение подписок из базы данных
async def get_subscriptions_from_db():
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        result = await conn.fetch(''' 
            SELECT user_id, subscription_type, periodicity, weekday, day_of_month, time, timezone_offset, 
            date_periodity, department, report_type 
            FROM subscriptions 
            WHERE periodicity = 'daily' OR periodicity = 'weekly' OR periodicity = 'monthly';
        ''')
        logging.info(f"Получено {len(result)} подписок из базы данных.")
        return result
    except Exception as e:
        logging.error(f"Ошибка при получении подписок: {e}")
        return []
    finally:
        await conn.close()

# Добавление задачи в планировщик
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
        department: str
):
    hour, minute = time_obj.hour, time_obj.minute
    logging.info(f"Добавление задачи для пользователя {user_id} на {hour}:{minute} для отчёта {sub_type}.")

    if periodicity == "daily":
        trigger = CronTrigger(hour=hour, minute=minute, timezone=pytz.timezone("Europe/Moscow"))
    elif periodicity == "weekly":
        trigger = CronTrigger(day_of_week=weekday, hour=hour, minute=minute, timezone=pytz.timezone("Europe/Moscow"))
    elif periodicity == "monthly":
        trigger = CronTrigger(day=day_of_month, hour=hour, minute=minute, timezone=pytz.timezone("Europe/Moscow"))
    else:
        raise ValueError(f"Неизвестная периодичность: {periodicity}")

    logging.info(f"Триггер для задачи: {trigger}")

    # Добавление задачи в планировщик
    scheduler.add_job(
        send_report,
        trigger,
        args=[bot, user_id, report_type, date_periodity, department],
        id=f"report_{user_id}_{sub_type}_{periodicity}_{hour}_{minute}",
        replace_existing=True
    )
    logging.info(f"Задача для пользователя {user_id} успешно добавлена в планировщик.")

# Отправка отчёта пользователю
async def send_report(
        bot: Bot,
        user_id: int,
        report_type: str,
        date_periodity: str,
        department: str  # здесь department — это токен (ID)
):
    logging.info(f"Запуск задачи: отправка отчёта {report_type} пользователю {user_id} за период {date_periodity}.")
    try:
        state_data = {
            "report:type": report_type,
            "report:period": date_periodity,
            "report:department": department
        }

        # Получаем название подразделения по его токену
        department_name = await get_department_name(user_id, department)  # <- Новая функция

        texts = await generate_report(tgid=user_id, state_data=state_data)
        caption = (
            f"Ваш отчёт ({report_type}) за период: {date_periodity}\n"
            f"Подразделение: {department_name}\n\n"  # <- Используем название вместо токена
        )

        for text in texts:
            parse_mode = "Markdown" if "**" in text else "HTML"
            await bot.send_message(user_id, caption + text, parse_mode=parse_mode)

        logging.info(f"Отчёт {report_type} успешно отправлен пользователю {user_id}.")
    except Exception as e:
        logging.error(f"Ошибка при отправке отчёта пользователю {user_id}: {e}")
        await bot.send_message(user_id, "Произошла ошибка при отправке отчёта. Попробуйте позже.")

# Запланировать все подписки
async def schedule_all_subscriptions(bot: Bot):
    subscriptions = await get_subscriptions_from_db()  # Извлекаем все подписки из базы данных
    for sub in subscriptions:
        if not sub.get('report_type'):  # Проверка на отсутствие report_type
            logging.error(f"Отсутствует report_type для подписки пользователя {sub['user_id']}")
            continue  # Пропустить эту подписку, если report_type отсутствует

        # Вставляем задачу в планировщик для каждого пользователя
        await add_subscription_task(
            bot=bot,
            user_id=sub['user_id'],
            sub_type=sub['subscription_type'],
            periodicity=sub['periodicity'],
            weekday=sub['weekday'],
            day_of_month=sub['day_of_month'],
            time_obj=sub['time'],  # ensure this is a time object
            date_periodity=sub['date_periodity'],
            report_type=sub['report_type'],
            department=sub['department']
        )

# Функция для запуска планировщика
def start_scheduler():
    scheduler.start()
    logging.info("Планировщик запущен.")

# Для того, чтобы видеть логи работы планировщика, нужно настроить уровень логирования
logging.basicConfig(level=logging.INFO)
