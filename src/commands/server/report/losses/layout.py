from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from ..common_choices import report_period_msg
from .write_off.layout import router as write_off_router, write_off_layout_msg

router = Router(name=__name__)

router.include_routers(write_off_router)


class FSMLosses(StatesGroup):
    ask_report_type = State()
    ask_period = State()


async def losses_next(query: CallbackQuery, state: FSMContext):
    kb = IKM(inline_keyboard=[
        [IKB(text="Инвентаризация", callback_data="losses_inventory")],
        [IKB(text="Списания", callback_data="losses_write_off")]
    ])
    await state.set_state(FSMLosses.ask_report_type)
    await query.message.answer(text="Выберите отчёт:", reply_markup="kb")


@router.callback_query(FSMLosses.ask_report_type)
async def ask_period_handler(query: CallbackQuery, state: FSMContext):
    await state.update_data({'report_type': query.data})

    await report_period_msg(query, state)
    await state.set_state(FSMLosses.ask_period)

    await query.answer()


@router.callback_query(FSMLosses.ask_period)
async def fork(query: CallbackQuery, state: FSMContext):
    await state.update_data({'report_period': query.data})

    report_type = (await state.get_data())['report_type']

    match report_type:
        case "losses_write_off":
            await write_off_layout_msg(query, state)
        case _:
            pass

    await query.answer
