from aiogram.types import InlineKeyboardButton as IKB

from ..api import get_departments
from ..handlers.types.report_all_departments_types import ReportAllDepartmentTypes


async def all_departments(tgid: int) -> dict:
    departments: dict = await get_departments(tgid)
    departments.update({
        ReportAllDepartmentTypes.ALL_DEPARTMENTS_INDIVIDUALLY: "Вся сеть (по объектам отдельно)",
        ReportAllDepartmentTypes.SUM_DEPARTMENTS_TOTALLY: "Вся сеть (итого по объектам)"
    })
    return departments


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
    "writeoff": "Потери",
    "losses": "Закупки",
    "foodcost": "Фудкост/Наценка",
    "turnover": "Оборачиваемость остатков",
}


all_types = {
    "losses": "Закупки потери/прибыль ФАКТ",
    "loss-forecast": "Закупки потери/прибыль ПРОГНОЗ",
    "food-cost": "Фудкост",
    "inventory": "Инвентаризация",
    "write-off": "Списания",
    "markup": "Наценка",
    "test-type": "Тестовый вид отчёта",
    "revenue": "Выручка",
    "turnover": "Оборачиваемость остатков"
}


all_menu_buttons = [
    IKB(text="Показатели 📊 ", callback_data="report:show_parameters"),
    IKB(text="Анализ 🔎", callback_data="report:show_analysis"),
    IKB(text="Обратите внимание 👀", callback_data="report:show_negative"),
    IKB(text="Обратите внимание 👀", callback_data="report:show_negative_analysis"),
    IKB(text="Рекомендации 💡", callback_data="report:show_recommendations"),
]


menu_button_translations = {
    "parameters": "Показатели 📊",
    "analysis": "Анализ 🔎",
    "negative": "Обратите внимание 👀",
    "negative_analysis": "Обратите внимание 👀",
    "analysis_only_negative": "Обратите внимание 👀",
    "only_negative": "Обратите внимание 👀",
    "recommendations": "Рекомендации 💡"
}

all_time_periods = {
    "daily": "Ежедневно",
    "workdays": "По будням",
    "weekly": "Еженедельно",
    "monthly": "Ежемесячно"
}




