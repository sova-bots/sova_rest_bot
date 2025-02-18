from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from .report_util import report_periods, get_department_name, delete_state_messages, report_types, ReportRequestData

router = Router(name=__name__)


@router.callback_query(F.data == "report_period_choice")
async def report_period_callback_handler(query: CallbackQuery, state: FSMContext):
    await report_period_msg(query, state)
    await delete_state_messages(state)
    await query.answer()


# get department name from departments list
async def get_dep_name(departments: list, user_id: int) -> str:
    if len(departments) == 1:
        department_name = await get_department_name(departments[0], user_id)
    elif len(departments) == 0:
        department_name = "Вся сеть"
    else:
        department_name = "Вся сеть*"
    return department_name


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
    


async def common_period_msg(query: CallbackQuery, state: FSMContext, choose_from: dict, local_report_types: dict):
    request_data = ReportRequestData(query.from_user.id, (await state.get_data()))
    
    if request_data.report_type is None:
        await query.message.edit_text(
            text=f"Вернитесь в меню и выберите отчёт ещё раз",
            reply_markup=IKM(inline_keyboard=[[IKB(text="Назад ↩️", callback_data="report")]])
        )
        return

    kb = IKM(inline_keyboard=[
        [IKB(text=v, callback_data=k)] for k, v in choose_from.items()
    ])
    
    if len(request_data.departments) == 1:
        department_name = await get_department_name(request_data.departments[0], query.from_user.id)
    else:
        department_name = "Вся сеть"


    await query.message.edit_text(
        text=f"Выберите период для отчёта: <b>{local_report_types[request_data.report_type]}</b>\nОбъект: <b>{department_name}</b>",
        reply_markup=kb
    )


async def common_report_type_msg(query: CallbackQuery, state: FSMContext, choose_from: dict):
    request_data = ReportRequestData(query.from_user.id, (await state.get_data()))
    
    if request_data.report_type is None:
        await query.message.edit_text(
            text=f"Вернитесь в меню и выберите отчёт ещё раз",
            reply_markup=IKM(inline_keyboard=[[IKB(text="Назад ↩️", callback_data="report")]])
        )
        return

    kb = IKM(inline_keyboard=[
        [IKB(text=v, callback_data=k)] for k, v in choose_from.items()
    ])
    
    department_name = await get_dep_name(request_data.departments, query.from_user.id) 

    await query.message.edit_text(
        text=f"Выберите вид отчёта\nОбъект: <b>{department_name}</b>",
        reply_markup=kb
    )


async def common_report_layout_msg(query: CallbackQuery, state: FSMContext, kb: list[list[IKB]], local_periods: dict, local_report_types: dict):
    assert isinstance(query.message, Message)

    request_data = ReportRequestData(query.from_user.id, (await state.get_data()))

    period = local_periods[request_data.period]
    department_name = await get_dep_name(request_data.departments, query.from_user.id) 

    await state.set_state(None)
    await query.message.edit_text(
        text=f"Объект: <b>{department_name}</b>\nОтчёт: <b>{local_report_types[request_data.report_type]}</b>\nПериод: <b>{period}</b>", 
        reply_markup=IKM(inline_keyboard=kb)
    )



async def get_common_header_msg(query: CallbackQuery, state: FSMContext, department_name: str, local_periods: dict, local_report_types: dict) -> str:
    request_data = ReportRequestData(query.from_user.id, (await state.get_data()))
    period = local_periods[request_data.period]
    return f"<b>{department_name}</b>\nОтчёт: <b>{local_report_types[request_data.report_type]}</b>\nПериод: <b>{period}</b>"

