from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from ..report_util import *
from ..common_choices import report_period_msg
from .text import *
from .properties import *

from .analysis import router as analysis_router

router = Router(name=__name__)

router.include_routers(analysis_router)


async def revenue_next(query: CallbackQuery, state: FSMContext):
    await report_period_msg(query, state)


@router.callback_query(FSMReportGeneral.ask_report_period)
async def period_fork(query: CallbackQuery, state: FSMContext):

    period = query.data
    await state.update_data({'report_period': period})

    report_type, report_departments, report_period = await get_report_parameters_from_state(state)

    department_name = await get_department_name((await state.get_data())['report_department'], query.from_user.id)

    match period:
        case "last-day":
            await show_report_parameters(query, state)
        case _:
            kb = IKM(inline_keyboard=[
                [IKB(text="Показатели 📊 ", callback_data="revenue_show_parameters")],
                [IKB(text="Анализ 🔎", callback_data="revenue_analysis")],
                [IKB(text="Обратите внимание 👀", callback_data="report_show_parameters")],
                [IKB(text="Рекомендации 💡", callback_data="report_show_parameters")]
            ])
            
            text = f"Объект: <b>{department_name}</b>\nОтчёт <b>{report_types[report_type]}</b>\nПериод <b>{report_periods[report_period]}</b>\n\nВыберите представление отчёта:"
            
            await query.message.edit_text(text, reply_markup=kb)

    await state.set_state()

    await try_answer_query(query)


@router.callback_query(F.data == "revenue_show_parameters")
async def show_report_parameters_handler(query: CallbackQuery, state: FSMContext):
    await show_report_parameters(query, state)
    await query.answer()


async def show_report_parameters(query: CallbackQuery, state: FSMContext):
    data = await get_reports(query, state)

    kb = IKM(inline_keyboard=[
        [IKB(text="Назад ↩️", callback_data="report")]
    ])

    msgs = []

    for r in data["data"]:
        text = await make_text(r, revenue_properties, state)
        msg = await query.message.answer(text, reply_markup=None)
        msgs.append(msg)

    await state.update_data({'messages_to_delete': msgs})

    await query.message.answer("Вернуться назад?", reply_markup=kb)

    await query.message.delete()   


