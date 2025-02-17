from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from ..common_choices import common_period_msg, common_report_type_msg
from ...report.report_util import ReportRequestData
from .product.layout import product_next, router as product_router

router = Router(name=__name__)

router.include_routers(product_router)


local_report_types = {
    "losses/product", "Закупки потери ФАКТ",
}

local_periods = {
    "last-day": "Вчерашний день",
    "this-week": "Текущая неделя",
    "this-month": "Текущий месяц",
    "last-week": "Прошлая неделя",
    "last-month": "Прошлый месяц",
}

class FSMLosses(StatesGroup):
    ask_report = State()
    ask_period = State()


async def losses_next(query: CallbackQuery, state: FSMContext):
    await common_report_type_msg(
        query=query, 
        state=state, 
        choose_from=local_report_types
    )
    await state.set_state(FSMLosses.ask_report)


@router.callback_query(FSMLosses.ask_report)
async def ask_period(query: CallbackQuery, state: FSMContext):
    await common_period_msg(
        query=query, 
        state=state, 
        choose_from=local_periods,
        local_report_types=local_report_types
    )
    await state.set_state(FSMLosses.ask_period)


@router.callback_query(FSMLosses.ask_report)
async def fork(query: CallbackQuery, state: FSMContext):
    report_type = (await state.get_data()['report_type'])

    match report_type:
        case "losses/product":
            product_next(query, state)
        case _:
            pass

