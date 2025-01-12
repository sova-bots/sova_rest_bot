import requests

from datetime import datetime, timedelta

from src.log import logger
import config as cf
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from src.log import logger
import config as cf


report_types = {
    "revenue": "Выручка",
    "guests-checks": "Гости/чеки",
    "avg-check": "Средний чек",
    "write-off": "Списания",
    "dangerous-operations": "Опасные операции",
    "food-cost": "Фудкост",
    "turnover": "Оборачиваемость в днях",
    "losses": "Закупки",
}


reports_with_stores = [
    "revenue",
    "write-off",
    "losses",
    "food-cost",
    "turnover",
]


report_periods = {
    "last-day": "Вчерашний день",
    "this-week": "Текущая неделя",
    "this-month": "Текущий месяц",
    "this-year": "Текущий год",
    "last-week": "Прошлая неделя",
    "last-month": "Прошлый месяц",
    "last-year": "Прошлый год",
}


problem_ares_show_positive = ["write-off", "food-cost", "turnover"]
problem_ares_show_negative = ["guests-checks", "avg-check"]


class FSMReportGeneral(StatesGroup):
    idle = State()


def get_departments(token: str) -> list:
    req = requests.get(
        url=f"{cf.API_PATH}/api/departments",
        headers={"Authorization": f"Bearer {token}"},
    )
    if req.status_code != 200:
        logger.msg("ERROR", f"Could not get departments: {token=}")
        return []
    return req.json()['departments']


def get_dates(period: str) -> tuple[datetime.date, datetime.date] | None:
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
        case _:
            logger.msg("ERROR", f"Error SendReports UnknownReportPeriod: {period=}")
            return None
    
    return date_from, date_to


def request_get_reports(token: str, report_type: str, report_departments: list, period: str, group: str = "department") -> tuple[int, dict]:
    if period is not None:
        dates = get_dates(period)
        if dates is None:
            return 2, {"error": "Unknown period"}
        date_from, date_to = dates

    data = {
        "departments": report_departments,
        "group": group,
    }

    if report_type != "losses":
        data["dateFrom"] = date_from.isoformat()
        data["dateTo"] = date_to.isoformat()

    req = requests.post(
        url=f"{cf.API_PATH}/api/{report_type}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-type": "application/json",
        },
        json=data
    )
    if req.status_code != 200:
        logger.msg("ERROR", f"Error RequestGetReports: {req.text}\n{report_type=} {report_departments=} {period=} {token=}")
        return 2, req.json()
    
    result = req.json()
    return 0, result


def get_department_index(r: dict, token: str) -> int:
    departments = get_departments(token)
    for i in range(len(departments)):
        if departments[i]["name"] == r["label"]:
            return i


def get_report_parameters_from_state_data(state_data: dict) -> tuple[str, list, str] | None:
    report_type = state_data.get('report_type')
    report_department = state_data.get('report_department')
    report_period = state_data.get('report_period')

    a = "report_type" not in state_data.keys()
    b = "report_department" not in state_data.keys()
    c = "report_period" not in state_data.keys()
    if a or b or c:
        return None
    
    a = state_data["report_type"] is None
    b = state_data["report_department"] is None
    c = state_data["report_period"] is None
    if a or b or c:
        return None

    if report_department == "report_departments_all":
        report_departments = []
    else:
        report_departments = [report_department]

    return report_type, report_departments, report_period
