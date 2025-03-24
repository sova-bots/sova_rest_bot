
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from .layout_util import next_step, repeat_current_step, previous_step, enter_step
from .types.msg_data import MsgData
from .states import AnalyticReportStates
from .msg.messages import recommendations_msg, parameters_msg

from src.util.log import logger

router = Router(name=__name__)


async def clear_report_state_data(state: FSMContext) -> None:
    await state.update_data(
        {
            "report:branch": None, 
            "report:step": None, 
            "report:department": None, 
            "report:type": None, 
            "report:input": None,
            "report:period": None
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
        await state.update_data({"report:type": value, "report:step": -1})

    await state.update_data({"report:input": None})
    await state.set_state(None)

    await next_step(MsgData(msg=query.message, state=state, tgid=query.from_user.id))
    await query.answer()


# menu handlers
@router.callback_query(F.data == "report:show_parameters")
async def show_recommendations_handler(query: CallbackQuery, state: FSMContext) -> None:
    await parameters_msg(MsgData(msg=query.message, state=state, tgid=query.from_user.id))
    await query.answer()


@router.callback_query(F.data == "report:show_analysis")
async def show_recommendations_handler(query: CallbackQuery, state: FSMContext) -> None:
    await parameters_msg(MsgData(msg=query.message, state=state, tgid=query.from_user.id), type_prefix="analysis.")
    await query.answer()


@router.callback_query(F.data == "report:show_negative")
async def show_recommendations_handler(query: CallbackQuery, state: FSMContext) -> None:
    await parameters_msg(MsgData(msg=query.message, state=state, tgid=query.from_user.id), only_negative=True)
    await query.answer()
    
    
@router.callback_query(F.data == "report:show_negative_analysis")
async def show_recommendations_handler(query: CallbackQuery, state: FSMContext) -> None:
    await parameters_msg(MsgData(msg=query.message, state=state, tgid=query.from_user.id), type_prefix="analysis.", only_negative=True)
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
    

@router.callback_query(F.data == "report:back_previous_step")
async def back_previous_step_handler(query: CallbackQuery, state: FSMContext) -> None:
    await previous_step(MsgData(msg=query.message, state=state, tgid=query.from_user.id))
    await query.answer()


@router.callback_query(F.data == "report:back_to_enter_department")
async def back_to_enter_department_handler(query: CallbackQuery, state: FSMContext) -> None:
    await enter_step((MsgData(msg=query.message, state=state, tgid=query.from_user.id)), step=0, branch="enter_department")
    await query.answer()


@router.callback_query(F.data == "report:null")
async def null_handler(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
