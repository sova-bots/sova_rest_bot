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
from .report_util import *
from .report_keyboards import get_recommendations_kb
from .report_stores import ReportStoreCallbackData
from .text import *
from .report_recommendations import problem_ares_show_negative, problem_ares_show_positive
from .report_keyboards import get_report_kb

router = Router(name=__name__)


class FSMServerReportGet(StatesGroup):
    ask_report_type = State()
    ask_report_department = State()
    ask_report_period = State()


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

    report_type, report_departments, report_period = get_report_parameters_from_state_data(state_data)

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

    if len(data["data"]) == 0:
        await query.message.edit_text("Не удалось составить отчёт")
        return
    
    await state.update_data({"report": report})

    # Сообщение - вид отчёта
    await query.message.answer(f"<i>Отчёт: <b>{report_types.get(report_type)}</b></i> {f"<i>за {report_periods.get(report_period)}:</i> 👇" if report_periods.get(report_period) is not None else " 👇"}")
    await query.message.delete()

    # Сообщение - отчёт
    for report in data["data"]:
        text = get_report_text(report_type, report)
        kb = get_report_kb(token, report_type, report, len(data["data"]))
        await query.message.answer(text, reply_markup=IKM(inline_keyboard=kb))

    # Сообщение - итог
    if "sum" in data.keys() and len(data["data"]) > 1:
        report = data["sum"]
        text = get_report_text(report_type, report)
        rkb = get_recommendations_kb(report_type, report) + [[IKB(text='В меню отчётов ↩️', callback_data='report_menu')]]
        await query.message.answer(text, reply_markup=IKM(inline_keyboard=rkb))
    elif len(data["data"]) > 1:
        # кнопка "В меню отчётов"
        kb = [[IKB(text='В меню отчётов ↩️', callback_data='report_menu')]]
        await query.message.answer("Вернуться на главную?", reply_markup=IKM(inline_keyboard=kb))

    await state.set_state(FSMReportGeneral.idle)
    logger.info(f"SendReport: Success {user_id=}")
