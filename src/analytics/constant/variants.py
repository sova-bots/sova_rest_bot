from datetime import datetime, timedelta
from ..api import get_departments

import config as cf
from src.util.log import logger


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
}



def get_dates(period: str) -> tuple[datetime.date, datetime.date]:
    today = datetime.now(tz=cf.TIMEZONE).date()
    match period:
        case "last-day":
            date_from = today - timedelta(days=1)
            date_to = date_from
        case "this-week":
            date_from = today - timedelta(days=today.weekday())
            date_to = today
        case "this-month":
            date_from = today.replace(day=1)
            date_to = today
        case "this-year":
            date_from = today.replace(day=1, month=1)
            date_to = today
        case "last-week":
            date_from = today - timedelta(days=today.weekday()+7)
            date_to = today - timedelta(days=today.weekday()+1)
        case "last-month":
            date_from = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            date_to = today.replace(day=1) - timedelta(days=1)
        case "last-year":
            date_from = (today.replace(day=1, month=1) - timedelta(days=1)).replace(day=1, month=1)
            date_to = today.replace(day=1, month=1) - timedelta(days=1)
        case "last-last-week":
            date_from = today - timedelta(days=today.weekday()+7) - timedelta(days=7)
            date_to = today - timedelta(days=today.weekday()+1) - timedelta(days=7)
        case "last-last-month":
            date_from = ((today.replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(day=1)
            date_to = (today.replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)
        case "last-last-year":
            date_from = today.replace(day=1, month=1, year=today.year-2)
            date_to = today.replace(day=1, month=1, year=today.year-1) - timedelta(days=1)
        case _:
            logger.msg("ERROR", f"Error SendReports UnknownReportPeriod: {period=}")
            raise RuntimeError(f"Error SendReports UnknownReportPeriod: {period=}")
    return date_from, date_to




