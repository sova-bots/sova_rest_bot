from aiogram.types import Message, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.fsm.context import FSMContext

from .types.msg_data import MsgData
from ..constant.variants import all_departments, all_branches, all_types, all_periods
from .states import AnalyticReportStates


# util
def make_kb(all_choices: dict[str, str], indexes: list[int] = []) -> IKM:
    if indexes:
        items = list(all_choices.items())
        all_choices = {items[i][0]: items[i][1] for i in range(len(items)) if i in indexes}

    kb = [[IKB(text=_name, callback_data=_id)] for _id, _name in all_choices.items()]
    return IKM(inline_keyboard=kb)


# state functions
async def _set_input_state(state: FSMContext, input_key: str) -> None:
    await state.set_state(AnalyticReportStates.value_input)
    await state.update_data({"report:input": input_key})


# msg functions
async def department_msg(msg_data: MsgData) -> None:
    await _set_input_state(msg_data.state, "report:department")

    assert msg_data.tgid is not None, "tgid not specified"
    departments = await all_departments(msg_data.tgid)

    text = "Выберите подразделение"
    kb = make_kb(departments)
    await msg_data.msg.edit_text(text=text, reply_markup=kb)


async def branch_msg(msg_data: MsgData) -> None:
    await _set_input_state(msg_data.state, "report:branch")

    assert msg_data.tgid is not None, "tgid not specified"
    departments = await all_departments(msg_data.tgid)
    department_id = (await msg_data.state.get_data()).get("report:department")
    
    text = f"Укажите вид отчёта для <b>{departments.get(department_id)}</b>"
    kb = make_kb(all_branches)
    await msg_data.msg.edit_text(text=text, reply_markup=kb)


async def type_msg(msg_data: MsgData, type_indexes: list[int]) -> None:
    await _set_input_state(msg_data.state, "report:type")

    text = "Выберите"
    kb = make_kb(all_types, type_indexes)
    await msg_data.msg.edit_text(text=text, reply_markup=kb)


async def period_msg(msg_data: MsgData, period_indexes: list[int]) -> None:
    await _set_input_state(msg_data.state, "report:period")

    text = "Выберите"
    kb = make_kb(all_periods, period_indexes)
    await msg_data.msg.edit_text(text=text, reply_markup=kb)


async def test_msg(msg_data: MsgData) -> None:
    state_data = await msg_data.state.get_data()

    departments = await all_departments(msg_data.tgid)
    department_id = state_data.get("report:department")

    _department = departments.get(department_id)
    _type = state_data.get("report:type")
    _period = state_data.get("report:period")

    await msg_data.msg.answer(text=f"{_department=}\n\n{_type=}\n\n{_period=}")