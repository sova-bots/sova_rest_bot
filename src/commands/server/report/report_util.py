import requests
from asyncio import get_event_loop

from datetime import datetime, timedelta

from src.log import logger
import config as cf
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from aiogram.exceptions import TelegramBadRequest

from src.commands.server.util.db import user_tokens_db

from src.log import logger
import config as cf


report_types = {
    "revenue": "Выручка",
    "losses_new": "Потери",
    # "guests-checks": "Гости/чеки",
    # "avg-check": "Средний чек",
    # "write-off": "Списания",
    # "dangerous-operations": "Опасные операции",
    # "food-cost": "Фудкост",
    # "turnover": "Оборачиваемость в днях",
    # "losses": "Закупки",
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


class ReportRequestData:
    token: str
    report_type: str
    departments: list
    period: str
    group: str

    def __init__(self, user_id: int, state_data: dict, group: str = "department"):
        token = user_tokens_db.get_token(user_id)

        report_type, report_departments, report_period = get_report_parameters_from_state_data(state_data)

        self.token = token
        self.report_type = report_type
        self.departments = report_departments
        self.period = report_period
        self.group = group


class FSMReportGeneral(StatesGroup):
    idle = State()
    ask_report_type = State()
    ask_report_department = State()
    ask_report_period = State()


async def get_departments(tgid: int):
    token = user_tokens_db.get_token(tgid=str(tgid))
    loop = get_event_loop()
    departments = await loop.run_in_executor(None, request_get_departments, token)
    return departments


async def get_department_name(department_id: str, tgid: int):
    departments = await get_departments(tgid)

    for department in departments:
        if department['id'] == department_id:
            return department['name']


def request_get_departments(token: str) -> list:
    req = requests.get(
        url=f"{cf.API_PATH}/api/departments",
        headers={"Authorization": f"Bearer {token}"},
    )
    if req.status_code != 200:
        logger.msg("ERROR", f"Could not get departments: {token=}")
        return []
    return req.json()['departments'] + [{"id": "report_departments_all", "name": "Вся сеть"}]


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


    # logger.info(f"{data['dateFrom']=}, {data['dateTo']=}")
    # return

    req = requests.post(
        url=f"{cf.API_PATH}/api/{report_type}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-type": "application/json",
            "Connection": "keep-alive",
            "User-Agent": "SOVA-rest Bot"
        },
        json=data
    )
    if req.status_code != 200:
        logger.msg("ERROR", f"Error RequestGetReports: {req.text}\n{report_type=} {report_departments=} {period=} {token=}")
        return 2, req.json()

    result = req.json()
    return 0, result


async def execute_request_get_reports(query: CallbackQuery, token, report_type, departments, period, group: str = "department") -> dict:
    assert isinstance(query.message, Message)

    loop = get_event_loop()
    status_code, data = await loop.run_in_executor(
        None,
        request_get_reports,
        token, report_type, departments, period, group
    )

    if status_code == 2:
        if "error" not in data.keys():
            await query.message.edit_text("Ошибка")
            raise Exception("Could not get report")

        match data["error"]:
            case "Wrong token":
                kb = IKM(inline_keyboard=[[IKB(text="Выйти и войти в систему 🔄️", callback_data="server_report_reauth")]])
                await query.message.edit_text("Ошибка, попробуйте переавторизоваться", reply_markup=kb)
            case _:
                raise Exception(f"Could not get report: {data["error"]}")
        return

    if len(data["data"]) == 0:
        await query.message.edit_text("Не удалось составить отчёт")
        raise Exception("Could not get report")

    return data


async def get_reports_from_data(query: CallbackQuery, data: ReportRequestData) -> dict:
    token = data.token
    user_id = query.from_user.id
    report_type = data.report_type
    departments = data.departments
    period = data.period
    group = data.group

    logger.info(f"SendReport: {user_id=} {report_type=} {period=} {token=}")

    reports = await execute_request_get_reports(query, token, report_type, departments, period, group)

    logger.info(f"ReportRecieved: {user_id=} {report_type=} {period=} {token=}")

    return reports


async def get_reports(query: CallbackQuery, state: FSMContext, group: str = "department") -> dict:
    assert isinstance(query.message, Message)

    await query.message.edit_text("Загрузка... ⚙️")

    state_data = await state.get_data()

    return await get_reports_from_data(query, data=ReportRequestData(query.from_user.id, state_data, group))



def get_department_index(r: dict, token: str) -> int:
    departments = get_departments(token)
    for i in range(len(departments)):
        if departments[i]["name"] == r["label"]:
            return i
    return -1


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


async def get_report_parameters_from_state(state: FSMContext) -> tuple[str, list, str] | None:
    return get_report_parameters_from_state_data((await state.get_data()))


async def delete_state_messages(state: FSMContext):
    if 'messages_to_delete' in (await state.get_data()).keys() and (await state.get_data())['messages_to_delete'] is not None:
        msg_list = (await state.get_data())['messages_to_delete']

        for msg in msg_list:
            await msg.delete()

        await state.update_data({'messages_to_delete': None})


async def try_answer_query(query: CallbackQuery, text: str | None = None) -> None:
    try:
        await query.answer(text)
    except TelegramBadRequest as e:
        logger.msg("WARNING", f"TelegramBadRequest: {e}")
