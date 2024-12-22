from asyncio import get_event_loop
from datetime import datetime, timedelta

import requests
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

import config as cf
from src.commands.server.util.db import user_tokens_db
from src.log import logger
from .report_recommendations import get_revenue_recommendation_types, RecommendationCallbackData
from .text import *

router = Router(name=__name__)


report_types = {
    "revenue": "Выручка",
    "guests-checks": "Гости/чеки",
    "avg-check": "Средний чек",
    "write-off": "Списания",
    "food-cost": "Фудкост",
    "turnover": "Оборачиваемость в днях",
    "losses": "Общие потери/экономия закупки",
}


report_periods = {
    "last-day": "Вчерашний день",
    "this-week": "Текущая неделя",
    "this-month": "Текущий месяц",
    "this-year": "Текущий год",
    "last-week": "Прошлая неделя",
    "last-month": "Прошлый месяц",
    "last-year": "Прошлый год",
}


class FSMServerReportGet(StatesGroup):
    ask_report_type = State()
    ask_report_department = State()
    ask_report_period = State()


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


def request_get_reports(token: str, report_type: str, report_departments: list , period: str) -> tuple[int, dict]:
    if period is not None:
        dates = get_dates(period)
        if dates is None:
            return 2, {"error": "Unknown period"}
        date_from, date_to = dates

    data = {"departments": report_departments}

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
    return 0, req.json()


@router.callback_query(F.data == "server_report_get")
async def choose_report_type(query: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = IKM(inline_keyboard=[
        [IKB(text=v, callback_data=k)] for k, v in report_types.items()
    ])
    await state.set_state(FSMServerReportGet.ask_report_type)
    await query.message.answer("Выберите вид отчёта", reply_markup=kb)
    await query.answer()


@router.callback_query(FSMServerReportGet.ask_report_type)
async def choose_report_department(query: CallbackQuery, state: FSMContext):
    await state.update_data({'report_type': query.data})

    token = user_tokens_db.get_token(tgid=query.from_user.id)

    loop = get_event_loop()
    departments = await loop.run_in_executor(None, get_departments, token)

    kb = IKM(inline_keyboard=[
        [IKB(text=department['name'], callback_data=department['id'])] for department in departments
    ] + [[IKB(text="Все объекты", callback_data="report_departments_all")]])
    await state.set_state(FSMServerReportGet.ask_report_department)
    await query.message.edit_text("Выберите подразделение", reply_markup=kb)
    await query.answer()


@router.callback_query(FSMServerReportGet.ask_report_department)
async def choose_report_period(query: CallbackQuery, state: FSMContext):
    await state.update_data({'report_department': query.data})

    report_type = (await state.get_data()).get('report_type')

    if report_type == "losses":
        await send_reports(query, state)
        return

    kb = IKM(inline_keyboard=[
        [IKB(text=v, callback_data=k)] for k, v in report_periods.items()
    ])
    await state.set_state(FSMServerReportGet.ask_report_period)
    await query.message.edit_text("Выберите период отчёта", reply_markup=kb)
    await query.answer()


@router.callback_query(FSMServerReportGet.ask_report_period)
async def get_period(query: CallbackQuery, state: FSMContext):
    await state.update_data({'report_period': query.data})
    await query.answer()
    await send_reports(query, state)


async def send_reports(query: CallbackQuery, state: FSMContext):
    await query.message.edit_text("Загрузка... ⚙️")

    user_id = query.from_user.id
    token = user_tokens_db.get_token(user_id)
    state_data = await state.get_data()

    report_type = state_data.get('report_type')

    report_department = state_data.get('report_department')
    if report_department == "report_departments_all":
        report_departments = []
    else:
        report_departments = [report_department]

    report_period = state_data.get('report_period')

    await state.clear()

    logger.info(f"SendReport: {user_id=} {report_type=} {report_period=} {token=}")

    loop = get_event_loop()
    status_code, data = await loop.run_in_executor(
        None, 
        request_get_reports, 
        token, report_type, report_departments, report_period
    )

    if status_code == 2:
        if "error" not in data.keys():
            await query.message.edit_text("Ошибка")
            return

        match data["error"]:
            case "Wrong token":
                kb = IKM(inline_keyboard=[[IKB(text="Выйти и войти в систему 🔄️", callback_data="server_report_reauth")]])
                await query.message.edit_text("Ошибка, попробуйте переавторизоваться", reply_markup=kb)
            case _:
                await query.message.edit_text("Ошибка")
        return

    if len(data.get('report')) == 0:
        await query.message.edit_text("Не удалось составить отчёт")
        return

    text = ""
    for report in data.get('report'):
        match report_type:
            case "revenue":
                text += report_revenue_text(report)
            case "guests-checks":
                text += report_guests_checks_text(report)
            case "avg-check":
                text += report_avg_check_text(report)
            case "write-off":
                text += report_write_off_text(report)
            case "food-cost":
                text += report_food_cost_text(report)
            case "turnover":
                text += report_turnover_text(report)
            case "losses":
                text += report_losses_text(report)
            case _:
                logger.msg("ERROR", f"Error SendReports UnknownReportType: {report_type=}")
                await query.message.answer("Ошибка")
                return
        text += "\n\n\n"

    ikb = [[IKB(text='В меню отчётов ↩️', callback_data='report_menu')]]

    if report_type == "revenue" and len(data.get('report')) == 1:
        report = data.get('report')[0]
        recommendation_types = get_revenue_recommendation_types(
            report['dynamics_week'],
            report['dynamics_month'],
            report['dynamics_year'],
        )
        if len(recommendation_types) > 0:
            ikb += [[IKB(text="Рекомендации 🔎", callback_data=RecommendationCallbackData(recs_types=recommendation_types, report_type=report_type).pack())]]

    # Сообщение - вид отчёта
    await query.message.answer(f"<i>Отчёт: <b>{report_types.get(report_type)}</b></i> {f"<i>за {report_periods.get(report_period)}:</i> 👇" if report_periods.get(report_period) is not None else " 👇"}")
    await query.message.delete()

    # Сообщение - отчёт
    kb = IKM(inline_keyboard=ikb)
    await query.message.answer(text, reply_markup=kb)

    logger.info(f"SendReport: Success {user_id=}")

# @router.message(Command('server_get_report'))
# async def get_report(msg: Message):
#     database = db.user_tokens_db
#     token = database.get_token(tgid=str(msg.from_user.id))
#
#     loading_msg = await msg.answer("...")
#
#     req = await send_request_to_get_reports(token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiIxIiwic2x1ZyI6IlJPR0FMSUsiLCJpYXQiOjE3MzM3NTMzOTgsImV4cCI6MTczMzgzOTc5OH0.LtUIvj0WHrLRw9D3IMOBdPOuKatIqOyYnVm3D760dsA")
#
#     if req.status_code != 200:
#         await loading_msg.edit_text(f"Error: {req.status_code}")
#         return
#
#     text = ""
#     for rep in req.json()['report']:
#         text += f"\n{rep}\n"
#
#     await loading_msg.edit_text(text)
