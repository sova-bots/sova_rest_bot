from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from .write_off.layout import router as write_off_router, write_off_layout_msg
from ..report_util import get_department_name

router = Router(name=__name__)

router.include_routers(write_off_router)


report_types = {
    "write-off": "Списания",
    "inventory": "Инвенторизация",
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


class FSMWriteOff(StatesGroup):
    ask_report_type = State()
    ask_period = State()


async def write_off_next(query: CallbackQuery, state: FSMContext):
    kb = IKM(inline_keyboard=[[IKB(text=v, callback_data=k)] for k, v in report_types.items()])
    await state.set_state(FSMWriteOff.ask_report_type)
    await query.message.edit_text(text="Выберите отчёт:", reply_markup=kb)


@router.callback_query(FSMWriteOff.ask_report_type)
async def ask_period_handler(query: CallbackQuery, state: FSMContext):
    await state.update_data({'report_type': query.data})

    await report_period_msg(query, state)
    await state.set_state(FSMWriteOff.ask_period)

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


@router.callback_query(FSMWriteOff.ask_period)
async def fork(query: CallbackQuery, state: FSMContext):
    await state.update_data({'report_period': query.data})

    report_type = (await state.get_data())['report_type']

    match report_type:
        case "write-off":
            await write_off_layout_msg(query, state)
        case "inventory":
            pass
        case _:
            pass

    await query.answer()
