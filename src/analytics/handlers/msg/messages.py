from aiogram.types import Message, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode

from .msg_util import set_input_state, make_kb
from ..types.msg_data import MsgData
from .headers import make_header
from ...constant.variants import all_departments, all_branches, all_types, all_periods
from ..states import AnalyticReportStates


# msg functions
async def department_msg(msg_data: MsgData) -> None:
    await set_input_state(msg_data.state, "report:department")

    assert msg_data.tgid is not None, "tgid not specified"
    departments = await all_departments(msg_data.tgid)

    header = await make_header(msg_data) + "\n\n"
    text = header + "Выберите подразделение"
    kb = make_kb(departments)
    await msg_data.msg.edit_text(text=text, reply_markup=kb)


async def branch_msg(msg_data: MsgData) -> None:
    await set_input_state(msg_data.state, "report:branch")

    assert msg_data.tgid is not None, "tgid not specified"
    departments = await all_departments(msg_data.tgid)
    department_id = (await msg_data.state.get_data()).get("report:department")
    
    header = await make_header(msg_data) + "\n\n"
    text = header + "Укажите вид отчёта"
    kb = make_kb(all_branches)
    await msg_data.msg.edit_text(text=text, reply_markup=kb)


async def type_msg(msg_data: MsgData, type_indexes: list[int]) -> None:
    await set_input_state(msg_data.state, "report:type")

    header = await make_header(msg_data) + "\n\n"
    text = header + "Выберите"
    kb = make_kb(all_types, type_indexes)
    await msg_data.msg.edit_text(text=text, reply_markup=kb)


async def period_msg(msg_data: MsgData, period_indexes: list[int]) -> None:
    await set_input_state(msg_data.state, "report:period")

    header = await make_header(msg_data) + "\n\n"
    text = header + "Выберите"
    kb = make_kb(all_periods, period_indexes)
    await msg_data.msg.edit_text(text=text, reply_markup=kb)


async def test_msg(msg_data: MsgData) -> None:
    state_data = await msg_data.state.get_data()

    departments = await all_departments(msg_data.tgid)
    department_id = state_data.get("report:department")

    _department = departments.get(department_id)
    _type = state_data.get("report:type")
    _period = state_data.get("report:period")

    await msg_data.msg.edit_text(text=f"{_department=}\n\n{_type=}\n\n{_period=}")
    
    
    
    