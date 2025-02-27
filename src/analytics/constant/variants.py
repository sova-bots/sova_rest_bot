from aiogram.types import InlineKeyboardButton as IKB

from ..api import get_departments


async def all_departments(tgid: int) -> dict:
    return await get_departments(tgid)


all_periods = {
    "last-day": "Вчерашний день",
    "this-week": "Текущая неделя",
    "this-month": "Текущий месяц",
    "this-year": "Текущий год",
    "last-week": "Прошлая неделя",
    "last-month": "Прошлый месяц",
    "last-year": "Прошлый год",
}


all_branches = {
    "revenue": "Выручка",
    "write-off": "Потери",
    "losses": "Закупки",
    "food-cost": "Фудкост/Наценка",
    "turnover": "Оборачиваемость остатков",
}


all_types = {
    "losses": "Закупки потери/прибыль ФАКТ",
    "loss-forecast": "Закупки потери/прибыль ПРОГНОЗ",
    "test-type": "Тестовый вид отчёта",
}


all_menu_buttons = [
    IKB(text="Показатели 📊 ", callback_data="report:show_parameters"),
    IKB(text="Анализ 🔎", callback_data="report:show_analysis"),
    IKB(text="Обратите внимание 👀", callback_data="report:show_negative"),
    IKB(text="Рекомендации 💡", callback_data="report:show_recommendations")
]




