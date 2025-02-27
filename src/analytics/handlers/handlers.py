
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from .layout_util import next_step, repeat_current_step
from .types.msg_data import MsgData
from .states import AnalyticReportStates
from .msg.messages import recommendations_msg

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


# menu handlers
@router.callback_query(F.data == "report:show_parameters")
async def show_recommendations_handler(query: CallbackQuery, state: FSMContext) -> None:
    await parameters_msg(MsgData(msg=query.message, state=state, tgid=query.from_user.id))
    await query.answer()


@router.callback_query(F.data == "report:show_recommendations")
async def show_recommendations_handler(query: CallbackQuery, state: FSMContext) -> None:
    await recommendations_msg(MsgData(msg=query.message, state=state, tgid=query.from_user.id))
    await query.answer()


# back buttons handlers
@router.callback_query(F.data == "report:back_current_step")
async def back_current_step_handler(query: CallbackQuery, state: FSMContext) -> None:
    await repeat_current_step(MsgData(msg=query.message, state=state, tgid=query.from_user.id))
    await query.answer()
