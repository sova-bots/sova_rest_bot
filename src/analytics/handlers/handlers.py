from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from .layout_util import next_step, repeat_current_step, previous_step, enter_step
from .types.msg_data import MsgData
from .states import AnalyticReportStates
from .msg.messages import recommendations_msg, parameters_msg
from .types.report_format_types import ReportFormatTypes

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


# back buttons handlers
@router.callback_query(F.data == "report:back_current_step")
async def back_current_step_handler(query: CallbackQuery, state: FSMContext) -> None:
    await repeat_current_step(MsgData(msg=query.message, state=state, tgid=query.from_user.id))
    await query.answer()


@router.callback_query(F.data == "report:back_previous_step")
async def back_previous_step_handler(query: CallbackQuery, state: FSMContext) -> None:
    state_data = await state.get_data()
    step = state_data.get("report:step", 0)

    if step <= 0:
        from src.basic.commands.start_command import get_markup
        await clear_report_state_data(state)
        await query.message.edit_text(
            "Вас приветствует чат-бот SOVA-tech!",
            reply_markup=get_markup(user_id=query.from_user.id, has_token=True)
        )
    else:
        await previous_step(MsgData(msg=query.message, state=state, tgid=query.from_user.id))

    await query.answer()


@router.callback_query(F.data == "report:back_to_enter_department")
async def back_to_enter_department_handler(query: CallbackQuery, state: FSMContext) -> None:
    await enter_step((MsgData(msg=query.message, state=state, tgid=query.from_user.id)), step=0,
                     branch="enter_department")
    await query.answer()


@router.callback_query(F.data == "report:null")
async def null_handler(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()


# value input
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
    await query.answer()
    await state.update_data({"report:format_type": ReportFormatTypes.PARAMETERS})
    await parameters_msg(MsgData(msg=query.message, state=state, tgid=query.from_user.id))


@router.callback_query(F.data == "report:show_analysis")
async def show_recommendations_handler(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await state.update_data({"report:format_type": ReportFormatTypes.ANALYSIS})
    await parameters_msg(MsgData(msg=query.message, state=state, tgid=query.from_user.id), type_prefix="analysis.")


@router.callback_query(F.data == "report:show_negative")
async def show_recommendations_handler(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await state.update_data({"report:format_type": ReportFormatTypes.ONLY_NEGATIVE})
    await parameters_msg(MsgData(msg=query.message, state=state, tgid=query.from_user.id), only_negative=True)


@router.callback_query(F.data == "report:show_negative_analysis")
async def show_recommendations_handler(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await state.update_data({"report:format_type": ReportFormatTypes.ANALYSIS_ONLY_NEGATIVE})
    await parameters_msg(MsgData(msg=query.message, state=state, tgid=query.from_user.id), type_prefix="analysis.",
                         only_negative=True)


@router.callback_query(F.data == "report:show_recommendations")
async def show_recommendations_handler(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await state.update_data(
        {"report:format_type": ReportFormatTypes.RECOMMENDATIONS})  # Вроде тут не надо, но пусть будет
    await recommendations_msg(MsgData(msg=query.message, state=state, tgid=query.from_user.id))


@router.callback_query(F.data == "report:back_to_main_menu")
async def back_to_main_menu_handler(query: CallbackQuery, state: FSMContext) -> None:
    from src.basic.commands.start_command import get_markup  # корректный импорт

    await clear_report_state_data(state)

    # Тут передай user_id и has_token (если не знаешь has_token — можно временно True)
    await query.message.edit_text(
        "Вас приветствует чат-бот SOVA-tech!",
        reply_markup=get_markup(user_id=query.from_user.id, has_token=True)
    )
    await query.answer()

