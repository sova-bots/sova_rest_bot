from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from .handlers import clear_report_state_data
from .layout_util import enter_step
from .types.msg_data import MsgData

router = Router(name=__name__)


@router.callback_query(F.data == "analytics_report_begin")
async def analytics_begin_handler(query: CallbackQuery, state: FSMContext) -> None:
    await clear_report_state_data(state)

    await enter_step(msg_data=MsgData(msg=query.message, state=state, tgid=query.from_user.id), branch="enter_department", step=0)

    await query.answer()


