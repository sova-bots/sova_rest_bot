import requests
from asyncio import get_event_loop

from aiogram import Router, F
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from .report_util import get_departments
from .text import get_report_text
from src.log import logger
from src.commands.server.util.db import user_tokens_db
import config as cf
from .report_util import *

router = Router(name=__name__)


class ReportStoreCallbackData(CallbackData, prefix="rprt-store"):
    department_index: str


class ReportChosenStoreCallbackData(CallbackData, prefix="rprt-chsn-store"):
    department_index: str
    store_index: str


class ReportBackToStoreCallbackData(CallbackData, prefix="rprt-back-store"):
    department_index: str


class FSMServerReportStores(StatesGroup):
    store_input = State()


@router.callback_query(ReportStoreCallbackData.filter(), FSMReportGeneral.idle)
async def get_stores_report(query: CallbackQuery, callback_data: ReportStoreCallbackData, state: FSMContext):
    msg = await query.message.answer("Загрузка... ⚙️")

    user_id = query.from_user.id
    token = user_tokens_db.get_token(user_id)

    department_id = get_departments(token)[int(callback_data.department_index)].get("id")

    state_data = await state.get_data()

    report_type = state_data.get('report_type')
    report_departments = [department_id]
    report_period = state_data.get('report_period')
    group = "store"

    # проверка на наличие данных в state
    if report_type is None: 
        await msg.edit_text("Перезайдите в меню отчётов и получите отчёт ещё раз", reply_markup=IKM(inline_keyboard=[[IKB(text='В меню отчётов ↩️', callback_data='report_menu')]]))
        return

    logger.info(f"SendReportStores: {user_id=} {report_type=} {report_departments=} {report_period=} {token=}")

    await query.answer()

    loop = get_event_loop()
    status_code, data = await loop.run_in_executor(
        None, 
        request_get_reports, 
        token, report_type, report_departments, report_period, group
    )

    if status_code != 0:
        print(data, status_code)
        logger.msg("ERROR", f"Error SendReportStores: {user_id=} {report_type=} {report_departments=} {report_period=} {token=}")
        query.answer("Ошибка")
        return

    await state.update_data({"stores": data})

    kb = []

    for i in range(len(data["data"])):
        store_data = data["data"][i]
        kb.append([IKB(text=store_data["label"], callback_data=ReportChosenStoreCallbackData(store_index=str(i), department_index=callback_data.department_index).pack())])

    await state.set_state(FSMServerReportStores.store_input)

    await msg.edit_text("Выберите склад", reply_markup=IKM(inline_keyboard=kb))



@router.callback_query(ReportChosenStoreCallbackData.filter(), FSMServerReportStores.store_input)
async def show_store_data(query: CallbackQuery, callback_data: ReportChosenStoreCallbackData, state: FSMContext):
    state_data = await state.get_data()
    
    # проверка на наличие данных в state
    if "stores" not in state_data.keys():
        await query.message.edit_text("Перезайдите в меню отчётов и получите отчёт ещё раз", reply_markup=IKM(inline_keyboard=[[IKB(text='В меню отчётов ↩️', callback_data='report_menu')]]))
        return

    store_report = state_data["stores"]["data"][int(callback_data.store_index)]

    report_type = state_data.get('report_type')

    # проверка на наличие данных в state
    if report_type is None: 
        await query.message.edit_text("Перезайдите в меню отчётов и получите отчёт ещё раз", reply_markup=IKM(inline_keyboard=[[IKB(text='В меню отчётов ↩️', callback_data='report_menu')]]))
        return
    
    # кнопка "К складам" (выбрать другой склад)
    kb = [[IKB(text="К складам 🔼", callback_data=ReportBackToStoreCallbackData(department_index=callback_data.department_index).pack())]]

    # кнопка "В меню отчётов"
    kb += [[IKB(text='В меню отчётов ↩️', callback_data='report_menu')]]

    await state.set_state(FSMReportGeneral.idle)

    await query.message.edit_text(text=str(get_report_text(report_type, store_report)), reply_markup=IKM(inline_keyboard=kb))
    await query.answer()


@router.callback_query(ReportBackToStoreCallbackData.filter(), FSMReportGeneral.idle)
async def back_to_stores(query: CallbackQuery, callback_data: ReportChosenStoreCallbackData, state: FSMContext):

    state_data = await state.get_data()

    # проверка на наличие данных в state
    if "stores" not in state_data.keys() or state_data["stores"] is None:
        await query.message.edit_text("Перезайдите в меню отчётов и получите отчёт ещё раз", reply_markup=IKM(inline_keyboard=[[IKB(text='В меню отчётов ↩️', callback_data='report_menu')]]))
        return
    
    data = state_data["stores"]

    kb = []
    for i in range(len(data["data"])):
        store_data = data["data"][i]
        kb.append([IKB(text=store_data["label"], callback_data=ReportChosenStoreCallbackData(store_index=str(i), department_index=callback_data.department_index).pack())])

    await state.set_state(FSMServerReportStores.store_input)

    await query.message.edit_text("Выберите склад", reply_markup=IKM(inline_keyboard=kb))
    await query.answer()
