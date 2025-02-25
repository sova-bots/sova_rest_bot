import asyncio
from asyncio.exceptions import CancelledError

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from src.analytics.db.db import user_tokens_db
from src.mailing.notification.sender import NotificationSender
from src.analytics.db import db

import config as cf
from src.util.log import logger
from src.basic.commands.start_command import router as start_command_router
from src.mailing.commands.registration.register.registration_command import router as register_command_router
from src.mailing.commands.registration.unregister.unregistration_command import router as unregister_command_router
from src.mailing.commands.techsupport.send_techsupport_message_command import router as send_ts_message_router
from src.mailing.commands.techsupport.show_techsupport_messages import router as show_ts_messages_router
from src.mailing.commands.techsupport.answer_techsupport_message import router as answer_ts_message_router
from src.mailing.commands.techsupport.techsupport_menu import router as techsupport_menu_router

from src.analytics.router import analytics_router

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
    analytics_router
]

dp = Dispatcher()


@router.message(Command("test"))
async def test_command(message: Message):
    await message.answer("sleep 5")
    await asyncio.sleep(5)
    await message.answer("sleep end")


async def include_routers() -> None:
    for router in routers:
        dp.include_router(router)


async def main() -> None:
    bot = Bot(token=cf.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.delete_webhook()
    await include_routers()

    if cf.notifications:
        sender = NotificationSender(bot)
        sender.start()

    try:
        logger.info('bot is running!')
        await dp.start_polling(bot)
    except (CancelledError, KeyboardInterrupt, SystemExit):
        dp.shutdown()

        if cf.notifications:
            sender.stop()

        user_tokens_db.close()

        logger.info('stopping')


if __name__ == '__main__':
    asyncio.run(main())
