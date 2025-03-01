from aiogram import Router

from .commands.mailing.mailing_menu import router as mailing_menu_router

mailing_router = Router(name=__name__)

mailing_router.include_routers(
    mailing_menu_router,
)
