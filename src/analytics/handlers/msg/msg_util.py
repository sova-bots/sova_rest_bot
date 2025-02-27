from aiogram.types import Message, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.fsm.context import FSMContext
from ..states import AnalyticReportStates
from ..types.msg_data import MsgData


# util
def make_kb(all_choices: dict[str, str], indexes: list[int] = []) -> IKM:
    if indexes:
        items = list(all_choices.items())
        all_choices = {items[i][0]: items[i][1] for i in range(len(items)) if i in indexes}

    kb = [[IKB(text=_name, callback_data=_id)] for _id, _name in all_choices.items()]
    return IKM(inline_keyboard=kb)


def make_kb_report_menu(buttons: list[IKB], indexes: list[int] = []) -> IKM:
    if indexes:
        buttons = [buttons[i] for i in range(len(buttons)) if i in indexes]

    kb = [[button] for button in buttons]
    return IKM(inline_keyboard=kb)


async def add_messages_to_delete(msg_data: MsgData, messages: list) -> None:
    state_data = await msg_data.state.get_data()
    messages_to_delete = state_data.get("report:messages_to_delete")
    if messages_to_delete is None:
        messages_to_delete = []
    messages_to_delete += [msg.message_id for msg in messages]
    await msg_data.state.update_data({"report:messages_to_delete": messages_to_delete})


# state functions
async def set_input_state(state: FSMContext, input_key: str) -> None:
    await state.set_state(AnalyticReportStates.value_input)
    await state.update_data({"report:input": input_key})
    
       
# common buttons
back_current_step_btn = IKB(text="Назад ↩️", callback_data="report:back_current_step")

