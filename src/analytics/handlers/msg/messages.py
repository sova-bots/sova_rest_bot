from aiogram.types import Message, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode

from .msg_util import set_input_state, make_kb, make_kb_report_menu, back_current_step_btn, add_messages_to_delete
from ..types.msg_data import MsgData
from .headers import make_header
from ...api import get_reports
from ...constant.variants import all_departments, all_branches, all_types, all_periods, all_menu_buttons
from ...constant.text.recommendations import recommendations
from ..states import AnalyticReportStates
from ...constant.text.texts import text_functions, TextData


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


async def menu_msg(msg_data: MsgData, buttons_indexes: list[int]) -> None:
    header = await make_header(msg_data) + "\n\n"
    text = header + "Выберите"
    kb = make_kb_report_menu(all_menu_buttons, buttons_indexes)
    await msg_data.msg.edit_text(text=text, reply_markup=kb)


async def test_msg(msg_data: MsgData) -> None:
    state_data = await msg_data.state.get_data()

    departments = await all_departments(msg_data.tgid)
    department_id = state_data.get("report:department")

    _department = departments.get(department_id)
    _type = state_data.get("report:type")
    _period = state_data.get("report:period")

    await msg_data.msg.edit_text(text=f"{_department=}\n\n{_type=}\n\n{_period=}")
    
      
# menu messages
async def parameters_msg(msg_data: MsgData) -> None:
    state_data = await msg_data.state.get_data()
    
    report_type = state_data.get("report:type")

    period = state_data.get("report:period")
    
    loading_msg = await msg_data.msg.edit_text(text="Загрузка ⏳")
    
    reports = await get_reports(
        tgid=msg_data.tgid, 
        state_data=state_data
    )
    
    back_kb = IKM(inline_keyboard=[[back_current_step_btn]])

    if None in reports:
        await loading_msg.edit_text(text="Не удалось загрузить отчёт", reply_markup=back_kb)
        return
    
    header = await make_header(msg_data)
    header_msg = await msg_data.msg.answer(text=header)
    
    text_func = text_functions[report_type]
    text_msg = await msg_data.msg.answer(text=text_func(TextData(reports=reports, period=period)))
    
    await add_messages_to_delete(msg_data=msg_data, messages=[header_msg, text_msg])
    
    await msg_data.msg.answer(text="Вернуться назад?", reply_markup=back_kb)
    
    await loading_msg.delete()


async def recommendations_msg(msg_data: MsgData) -> None:
    state_data = await msg_data.state.get_data()
    
    report_type = state_data.get("report:type")
        
    back_kb = IKM(inline_keyboard=[[back_current_step_btn]])
        
    if report_type == "revenue":
        await msg_data.msg.edit_text(text="в разработке", reply_markup=back_kb)
        return
    
    text = "<b>Рекомендации 💡</b>\n" + recommendations.get(report_type)
    
    if text is None:
        await msg_data.msg.edit_text(text="Не удалось получить рекомендации", reply_markup=back_kb)
        return
    
    await msg_data.msg.edit_text(text=text, reply_markup=back_kb)
    
    