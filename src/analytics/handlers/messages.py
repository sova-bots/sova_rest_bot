from aiogram.types import Message, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.fsm.context import FSMContext

from .types.msg_data import MsgData
from ..constant.variants import all_departments, all_branches, all_types
from .states import AnalyticReportStates


async def _set_input_state(state: FSMContext, input_key: str) -> None:
    await state.set_state(AnalyticReportStates.value_input)
    await state.update_data({"report:input": input_key})


async def department_msg(msg_data: MsgData) -> None:
    await _set_input_state(msg_data.state, "report:department")
    assert msg_data.tgid is not None, "tgid not specified"
    departments = await all_departments(msg_data.tgid)
    kb = [[IKB(text=_name, callback_data=_id)] for _id, _name in departments.items()]
    await msg_data.msg.answer(text="Выберите подразделение", reply_markup=IKM(inline_keyboard=kb))


async def branch_msg(msg_data: MsgData) -> None:
    await _set_input_state(msg_data.state, "report:branch")

    assert msg_data.tgid is not None, "tgid not specified"
    departments = await all_departments(msg_data.tgid)
    department_id = (await msg_data.state.get_data()).get("report:department")
    
    text = f"Укажите вид отчёта для <b>{departments.get(department_id)}</b>"
    kb = [[IKB(text=_name, callback_data=_id)] for _id, _name in all_branches.items()]
    await msg_data.msg.answer(text=text, reply_markup=IKM(inline_keyboard=kb))


async def type_msg(msg_data: MsgData, subtype_indexes: list) -> None:
    await _set_input_state(msg_data.state, "report:type")

    text = "Выберите"
    kb = [[IKB(text=_name, callback_data=_id)] for _id, _name in all_types.items()]
    await msg_data.msg.answer(text=text, reply_markup=IKM(inline_keyboard=kb))


async def test_msg(msg_data: MsgData) -> None:
    _type = (await msg_data.state.get_data()).get("report:type")
    await msg_data.msg.answer(text=f"{_type=}")