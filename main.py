import asyncio
import logging
from asyncio.exceptions import CancelledError

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
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

from src.mailing.commands.registration.notifications.check_time import subscription_router, scheduler, start_scheduler, schedule_all_subscriptions
from src.mailing.commands.registration.notifications.sub_mail import save_time_router

# Подключаем роутеры
router = Router(name=__name__)

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
    subscription_router
]

# Инициализация диспетчера
dp = Dispatcher()

@router.message(Command("test"))
async def test_command(message: Message):
    await message.answer("sleep 5")
    await asyncio.sleep(5)
    await message.answer("sleep end")

# Функция для подключения роутеров
async def include_routers(dp: Dispatcher) -> None:
    for router in routers:
        dp.include_router(router)

async def on_start(bot: Bot):
    logging.info("Бот запускается...")
    # Подключаем планировщик и загружаем все подписки
    await schedule_all_subscriptions(bot)
    start_scheduler()  # Запуск планировщика

# Главная асинхронная функция
async def main() -> None:
    bot = Bot(token=cf.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    await bot.delete_webhook()

    # Подключаем все роутеры
    await include_routers(dp)

    # Запускаем планировщик
    await on_start(bot)  # Включаем планировщик и загружаем подписки

    # Если включены уведомления, запускаем отправку уведомлений
    if cf.notifications:
        sender = NotificationSender(bot)
        sender.start()

    try:
        logger.info('Бот запущен!')
        await dp.start_polling(bot)
    except (CancelledError, KeyboardInterrupt, SystemExit):
        # Остановка бота и планировщика при исключении
        dp.shutdown()

        if cf.notifications:
            sender.stop()

        # Останавливаем планировщик
        scheduler.shutdown()
        logging.info("Планировщик остановлен.")

        logger.info('Бот остановлен.')

if __name__ == '__main__':
    # Запускаем главную функцию
    asyncio.run(main())
