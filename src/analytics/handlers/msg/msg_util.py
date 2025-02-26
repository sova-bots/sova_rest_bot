from aiogram.types import Message, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.fsm.context import FSMContext
from ..states import AnalyticReportStates


# util
def make_kb(all_choices: dict[str, str], indexes: list[int] = []) -> IKM:
    if indexes:
        items = list(all_choices.items())
        all_choices = {items[i][0]: items[i][1] for i in range(len(items)) if i in indexes}

    kb = [[IKB(text=_name, callback_data=_id)] for _id, _name in all_choices.items()]
    return IKM(inline_keyboard=kb)


# state functions
async def set_input_state(state: FSMContext, input_key: str) -> None:
    await state.set_state(AnalyticReportStates.value_input)
    await state.update_data({"report:input": input_key})
    