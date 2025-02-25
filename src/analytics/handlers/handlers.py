
from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from ..constant.layout import layout
from .messages import MsgData
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


def get_msg_func(step: int, branch: str) -> callable:
    return layout.get(branch)[step]


async def enter_step(msg_data: MsgData, step: int, branch: str) -> None:
    logger.info(f"STEP: entering:  {branch=}, {step=}")

    await msg_data.state.update_data({"report:branch": branch, "report:step": step})
    msg_func = get_msg_func(step, branch)
    await msg_func(msg_data)


async def next_step(msg_data: MsgData) -> None:
    state_data = await msg_data.state.get_data()
    next_step = state_data.get("report:step") + 1
    await enter_step(msg_data, step=next_step, branch=state_data.get("report:branch"))


@router.callback_query(AnalyticReportStates.value_input)
async def value_input_handler(query: CallbackQuery, state: FSMContext) -> None:
    state_data = await state.get_data()
    
    await state.update_data({state_data["report:input"]: query.data})

    await next_step(MsgData(msg=query.message, state=state, tgid=query.from_user.id))

    await query.answer()

