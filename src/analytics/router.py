from aiogram import Router

from .auth.authorization import router as authorization_router
from .handlers.begin import router as begin_router
from .handlers.handlers import router as handlers_router

analytics_router = Router(name="analytics")

analytics_router.include_routers(
    authorization_router,
    begin_router,
    handlers_router,
)