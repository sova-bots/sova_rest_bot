from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from ...common_choices import common_period_msg, common_report_type_msg, common_report_layout_msg
from ....report.report_util import ReportRequestData
from ..layout import FSMLosses, local_periods, local_report_types

router = Router(name=__name__)


async def product_next(query: CallbackQuery, state: FSMContext):
    await common_report_layout_msg(
        query=query,
        state=state,
        local_report_types=local_report_types,
        local_periods=local_periods,
        kb = 
    )

