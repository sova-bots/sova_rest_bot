import asyncio
from asyncio.exceptions import CancelledError

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.notification.sender import NotificationSender

import config as cf
from src.log import logger
from src.commands.start.start_command import router as start_command_router
from src.commands.register.registration_command import router as register_command_router
from src.commands.unregister.unregistration_command import router as unregister_command_router
from src.commands.techsupport.send_techsupport_message_command import router as send_ts_message_router
from src.commands.techsupport.show_techsupport_messages import router as show_ts_messages_router
from src.commands.techsupport.answer_techsupport_message import  router as answer_ts_message_router

routers = [
    start_command_router,
    register_command_router,
    unregister_command_router,
    send_ts_message_router,
    show_ts_messages_router,
    answer_ts_message_router
]

dp = Dispatcher()


async def include_routers() -> None:
    for router in routers:
        dp.include_router(router)


async def main() -> None:
    bot = Bot(token=cf.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.delete_webhook()
    await include_routers()

    sender = NotificationSender(bot)
    sender.start()

    try:
        logger.info('bot is running!')
        await dp.start_polling(bot)
    except (CancelledError, KeyboardInterrupt, SystemExit):
        dp.shutdown()
        sender.stop()
        logger.info('stopping')


if __name__ == '__main__':
    asyncio.run(main())
