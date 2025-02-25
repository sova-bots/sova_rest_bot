from dataclasses import dataclass

from aiogram.types import Message, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.fsm.context import FSMContext

from ..constant.variants import all_departments
from .states import AnalyticReportStates

@dataclass
class MsgData:
    msg: Message
    state: FSMContext
    tgid: int | None = None


async def _set_input_state(state: FSMContext, input_key: str) -> None:
    await state.set_state(AnalyticReportStates.value_input)
    await state.update_data({"report:input": input_key})


async def department_msg(msg_data: MsgData) -> None:
    await _set_input_state(msg_data.state, "report:department")
    
    departments = await all_departments(msg_data.tgid)
    kb = [[IKB(text=_name, callback_data=_id)] for _id, _name in departments.items()]

    await msg_data.msg.answer(text="Заголовок!!!\nВыберите подразделение", reply_markup=IKM(inline_keyboard=kb))


async def test_msg(msg_data: MsgData) -> None:
    department = (await msg_data.state.get_data()).get("report:department")

    await msg_data.msg.answer(text=f"{department}")