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

from .revenue.layout import revenue_next, router as revenue_router

router = Router(name=__name__)

router.include_routers(revenue_router)


@router.callback_query(F.data == "report")
async def report_department_choice(query: CallbackQuery, state: FSMContext):

    await delete_state_messages(state)

    await state.clear()

    departments = await get_departments(tgid=query.from_user.id)

    kb = IKM(inline_keyboard=[
        [IKB(text=department['name'], callback_data=department['id'])] for department in departments]
    )

    await state.set_state(FSMReportGeneral.ask_report_department)

    await query.message.edit_text("Выберите интересующий вас объект или сеть целиком", reply_markup=kb)
    await query.answer()


@router.callback_query(FSMReportGeneral.ask_report_department)
async def report_type_choice(query: CallbackQuery, state: FSMContext):

    await state.update_data({"report_department": query.data})

    kb = IKM(inline_keyboard=[
        [IKB(text=v, callback_data=k)] for k, v in report_types.items()
    ])

    await state.set_state(FSMReportGeneral.ask_report_type)

    department_name = await get_department_name(query.data, query.from_user.id)

    await query.message.edit_text(f"Укажите вид отчёта для объекта: <b>{department_name}</b>", reply_markup=kb)
    await query.answer()


@router.callback_query(FSMReportGeneral.ask_report_type)
async def fork(query: CallbackQuery, state: FSMContext):

    report_type = query.data

    await state.update_data({'report_type': report_type})

    match report_type:
        case "revenue":
            await revenue_next(query, state)
        case "losses_new":
            await 
        case _:
            pass
    
    await query.answer()


# @router.callback_query(FSMServerReportGet.ask_report_period)
# async def get_period(query: CallbackQuery, state: FSMContext):
#     await state.update_data({'report_period': query.data})
#     await query.answer()
#     await send_reports(query, state)


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
            raise Exception("Could not get report")

        match data["error"]:
            case "Wrong token":
                kb = IKM(inline_keyboard=[[IKB(text="Выйти и войти в систему 🔄️", callback_data="server_report_reauth")]])
                await query.message.edit_text("Ошибка, попробуйте переавторизоваться", reply_markup=kb)
            case _:
                raise Exception("Could not get report")
        return

    if len(data["data"]) == 0:
        await query.message.edit_text("Не удалось составить отчёт")
    
    await state.update_data({"report": data})

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
        rkb = get_recommendations_kb(report_type, report) + [[IKB(text='В меню отчётов ↩️', callback_data='report')]]
        await query.message.answer(text, reply_markup=IKM(inline_keyboard=rkb))
    elif len(data["data"]) > 1:
        # кнопка "В меню отчётов"
        kb = [[IKB(text='В меню отчётов ↩️', callback_data='report')]]
        await query.message.answer("Вернуться на главную?", reply_markup=IKM(inline_keyboard=kb))

    await state.set_state(FSMReportGeneral.idle)
    logger.info(f"SendReport: Success {user_id=}")
