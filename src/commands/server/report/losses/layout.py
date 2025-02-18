from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from .local import FSMLosses, local_periods, local_report_types

from ..common_choices import common_period_msg, common_report_type_msg
from ...report.report_util import ReportRequestData
from .product.layout import product_next, router as product_router

router = Router(name=__name__)

router.include_routers(product_router)


async def losses_next(query: CallbackQuery, state: FSMContext):
    await common_report_type_msg(
        query=query, 
        state=state, 
        choose_from=local_report_types
    )
    await state.set_state(FSMLosses.ask_report)


@router.callback_query(FSMLosses.ask_report)
async def ask_period(query: CallbackQuery, state: FSMContext):
    await state.update_data({'report_type': query.data})

    await common_period_msg(
        query=query, 
        state=state, 
        choose_from=local_periods,
        local_report_types=local_report_types
    )
    await state.set_state(FSMLosses.ask_period)
    await query.answer()


@router.callback_query(FSMLosses.ask_period)
async def fork(query: CallbackQuery, state: FSMContext):
    print(query.data)
    await state.update_data({'report_period': query.data})

    report_type = (await state.get_data())['report_type']

    match report_type:
        case "losses/product":
            await product_next(query, state)
        case _:
            pass

    await query.answer()

