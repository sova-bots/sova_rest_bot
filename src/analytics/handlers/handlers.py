
from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from .layout import next_step
from .types.msg_data import MsgData
from .states import AnalyticReportStates

from src.util.log import logger

router = Router(name=__name__)


async def clear_report_state_data(state: FSMContext) -> None:
    await state.update_data(
        {
            "report:branch": None, 
            "report:step": None, 
            "report:department": None, 
            "report:type": None, 
            "report:input": None
        }
    )
    await state.set_state(None)


@router.callback_query(AnalyticReportStates.value_input)
async def value_input_handler(query: CallbackQuery, state: FSMContext) -> None:
    state_data = await state.get_data()

    key: str = state_data["report:input"]
    value: str = query.data
    await state.update_data({key: value})

    if key == "report:branch":
        await state.update_data({"report:step": -1})

    await state.update_data({"report:input": None})
    await state.set_state(None)

    await next_step(MsgData(msg=query.message, state=state, tgid=query.from_user.id))
    await query.answer()

