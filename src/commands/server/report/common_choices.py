from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from .report_util import *

router = Router(name=__name__)


@router.callback_query(F.data == "report_period_choice")
async def report_period_callback_handler(query: CallbackQuery, state: FSMContext):
    await report_period_msg(query, state)
    await delete_state_messages(state)
    await query.answer()


async def report_period_msg(query: CallbackQuery, state: FSMContext):

    if "report_type" not in (await state.get_data()).keys() or (await state.get_data())['report_type'] is None:
        await query.message.edit_text(
            text=f"Вернитесь в меню и выберите отчёт ещё раз",
            reply_markup=IKM(inline_keyboard=[[IKB(text="Назад ↩️", callback_data="report")]])
        )
        return

    report_type = (await state.get_data())['report_type']
    department_id = (await state.get_data())['report_department']

    kb = IKM(inline_keyboard=[
        [IKB(text=v, callback_data=k)] for k, v in report_periods.items()
    ])
    
    department_name = await get_department_name(department_id, query.from_user.id)

    await query.message.edit_text(
        text=f"Выберите период для отчёта: <b>{report_types[report_type]}</b>\nОбъект: <b>{department_name}</b>",
        reply_markup=kb
    )
    await state.set_state(FSMReportGeneral.ask_report_period)
