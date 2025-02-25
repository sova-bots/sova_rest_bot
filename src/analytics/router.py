from aiogram import Router

from .auth.authorization import router as authorization_router

analytics_router = Router(name="analytics")

analytics_router.include_routers(
    authorization_router,
)