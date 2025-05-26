import asyncio
import logging
from asyncio.exceptions import CancelledError
from datetime import datetime

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage

import config as cf
from src.util.log import logger
from src.mailing.notification.sender import NotificationSender

from src.basic.commands.start_command import router as start_command_router
from src.mailing.commands.registration.register.registration_command import router as register_command_router
from src.mailing.commands.registration.unregister.unregistration_command import router as unregister_command_router
from src.mailing.commands.techsupport.send_techsupport_message_command import router as send_ts_message_router
from src.mailing.commands.techsupport.show_techsupport_messages import router as show_ts_messages_router
from src.mailing.commands.techsupport.answer_techsupport_message import router as answer_ts_message_router
from src.mailing.commands.techsupport.techsupport_menu import router as techsupport_menu_router

from src.analytics.router import analytics_router
from src.mailing.mailing_router import mailing_router

from src.mailing.commands.registration.notifications.check_time import (
    scheduler,
    schedule_all_subscriptions,
    start_scheduler,
    subscription_router,
)
from src.mailing.commands.registration.notifications.sub_mail import save_time_router

from src.analytics.db.db import get_all_stop_departments, get_access_list_data

from src.generate_reports.sending_pdf_excel_reports import file_report_router, send_generated_report

from aiogram.types.input_file import BufferedInputFile


# Основной роутер
router = Router(name=__name__)

# Все маршруты бота
routers = [
    router,
    start_command_router,
    register_command_router,
    unregister_command_router,
    send_ts_message_router,
    show_ts_messages_router,
    answer_ts_message_router,
    techsupport_menu_router,
    analytics_router,
    mailing_router,
    save_time_router,
    subscription_router,
    file_report_router,
]

async def send_report_with_attachment(
        bot: Bot,
        user_id: int,
        report_type: str,
        period: str,
        department: str,
        format_type: str = "text"
):
    """Отправка отчета в выбранном формате (PDF/Excel)"""
    try:
        report_data = {
            "report:type": report_type,
            "report:period": period,
            "report:department": department,
            "report:format_type": format_type
        }

        if format_type == "pdf":
            pdf_bytes = await handle_send_pdf_report(user_id, report_data)
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            await bot.send_document(
                user_id,
                document=BufferedInputFile(pdf_bytes, filename=filename),
                caption=f"📊 Отчет {report_type} за {period}"
            )

        elif format_type == "excel":
            excel_bytes = await handle_send_excel_report(user_id, report_data)
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            await bot.send_document(
                user_id,
                document=BufferedInputFile(excel_bytes, filename=filename),
                caption=f"📊 Отчет {report_type} за {period}"
            )

        else:
            await handle_send_any_report(bot, user_id, report_type, period, department, format_type)

    except Exception as e:
        logger.error(f"Ошибка при генерации отчета: {e}")
        await bot.send_message(
            user_id,
            "⚠️ Произошла ошибка при генерации отчета. Попробуйте позже."
        )


async def include_routers(dp: Dispatcher) -> None:
    for r in routers:
        dp.include_router(r)


async def on_start(bot: Bot):
    logger.info("Бот запускается...")

    departments = await get_all_stop_departments()
    if departments:
        logger.info(f"Загружено стоп-отделений: {len(departments)}")
    else:
        logger.warning("Стоп-отделения не загружены")

    access_data = await get_access_list_data()
    if access_data:
        logger.info(f"Загружено пользователей с доступом: {len(access_data)}")
    else:
        logger.warning("Данные доступа не загружены")

    try:
        await schedule_all_subscriptions(bot)
        start_scheduler()
        logger.info("Планировщик рассылок запущен")
    except Exception as e:
        logger.error(f"Ошибка запуска планировщика: {e}")


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    bot = Bot(token=cf.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    await bot.delete_webhook(drop_pending_updates=True)
    await include_routers(dp)
    await on_start(bot)

    if cf.notifications:
        sender = NotificationSender(bot)
        sender.start()
        logger.info("Сервис уведомлений запущен")

    try:
        logger.info("Бот успешно запущен и готов к работе")
        await dp.start_polling(bot)
    except (CancelledError, KeyboardInterrupt, SystemExit):
        logger.info("Получен сигнал остановки...")

        await dp.shutdown()

        if cf.notifications:
            sender.stop()
            logger.info("Сервис уведомлений остановлен")

        scheduler.shutdown()
        logger.info("Планировщик рассылок остановлен")

        logger.info("Бот успешно завершил работу")


if __name__ == "__main__":
    asyncio.run(main())
