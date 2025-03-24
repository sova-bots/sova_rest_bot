import logging

from aiogram.types import Message, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode

from .msg_util import clear_report_state_data, set_input_state, make_kb, make_kb_report_menu, back_current_step_btn, add_messages_to_delete
from ..types.msg_data import MsgData
from .headers import make_header
from ...api import get_reports
from ...constant.variants import all_departments, all_branches, all_types, all_periods, all_menu_buttons
from ..text.recommendations import recommendations
from ..text.revenue_texts import revenue_analysis_text
from ..text.texts import text_functions
from ..types.text_data import TextData

from src.mailing.commands.registration.notifications.sub_mail import SubscriptionState

async def check_state_data(state: FSMContext):
    data = await state.get_data()
    logging.info(f"State data: {data}")


# msg functions
async def department_msg(msg_data: MsgData) -> None:
    state_data = await msg_data.state.get_data()
    logging.info(f"Состояние перед выбором подразделения: {state_data}")  # Логируем состояние перед выбором

    if state_data.get("report:step") == 0:
        await clear_report_state_data(msg_data.state)

    await set_input_state(msg_data.state, "report:department")

    departments = await all_departments(msg_data.tgid)

    header = await make_header(msg_data) + "\n\n"
    text = header + "Выберите подразделение"
    kb = make_kb(departments)
    await msg_data.msg.edit_text(text=text, reply_markup=kb)

    # Логируем состояние после установки
    await check_state_data(msg_data.state)



async def branch_msg(msg_data: MsgData) -> None:
    await set_input_state(msg_data.state, "report:branch")

    departments = await all_departments(msg_data.tgid)
    department_id = (await msg_data.state.get_data()).get("report:department")
    logging.info(f"Выбранное подразделение: {department_id}")  # Логируем выбранное подразделение

    header = await make_header(msg_data) + "\n\n"
    text = header + "Укажите вид отчёта"
    kb = make_kb(all_branches)
    await msg_data.msg.edit_text(text=text, reply_markup=kb)

    # Логируем состояние
    await check_state_data(msg_data.state)


async def type_msg(msg_data: MsgData, type_indexes: list[int]) -> None:
    await set_input_state(msg_data.state, "report:type")

    header = await make_header(msg_data) + "\n\n"
    text = header + "Выберите тип отчета"
    kb = make_kb(all_types, type_indexes)
    await msg_data.msg.edit_text(text=text, reply_markup=kb)

    # Сохраняем report_type в состоянии
    if type_indexes and type_indexes[0] in all_types:
        selected_type = all_types[type_indexes[0]]  # Получаем тип отчета по индексу
        await msg_data.state.update_data(report_type=selected_type)  # Сохраняем под ключом report_type
        logging.info(f"Пользователь {msg_data.tgid} выбрал тип отчета: {selected_type}")  # Логируем выбор типа
    else:
        logging.error(f"Неверный индекс типа отчета: {type_indexes}")  # Логируем ошибку
        await msg_data.msg.answer("Ошибка: неверный тип отчета.")
        return

    # Переходим к выбору периода данных отчета
    await msg_data.state.set_state(SubscriptionState.choosing_period)
    await msg_data.msg.answer("Теперь выберите период данных для отчета.")



async def period_msg(msg_data: MsgData, period_indexes: list[int]) -> None:
    await set_input_state(msg_data.state, "report:period")  # Устанавливаем состояние для выбора периода

    header = await make_header(msg_data) + "\n\n"
    text = header + "Выберите срок отчёта:"
    kb = make_kb(all_periods, period_indexes)  # Клавиатура с вариантами периодов
    await msg_data.msg.edit_text(text=text, reply_markup=kb)

    # Логируем состояние
    await check_state_data(msg_data.state)


async def menu_msg(msg_data: MsgData, buttons_indexes: list[int]) -> None:
    header = await make_header(msg_data) + "\n\n"
    text = header + "Выберите"

    kb = make_kb_report_menu(all_menu_buttons, buttons_indexes)

    await msg_data.msg.edit_text(text=text, reply_markup=kb)


async def test_msg(msg_data: MsgData) -> None:
    state_data = await msg_data.state.get_data()
    logging.info(f"Тестовое сообщение. Состояние: {state_data}")  # Логируем состояние в тестовом сообщении

    departments = await all_departments(msg_data.tgid)
    department_id = state_data.get("report:department")

    _department = departments.get(department_id)
    _type = state_data.get("report:type")
    _period = state_data.get("report:period")

    await msg_data.msg.edit_text(text=f"{_department=}\n\n{_type=}\n\n{_period=}")
    
      
# menu messages
async def parameters_msg(msg_data: MsgData, type_prefix: str = "", only_negative: bool = False, recommendations: bool = False) -> None:
    state_data = await msg_data.state.get_data()

    report_type = state_data.get("report:type")

    period = state_data.get("report:period")

    loading_msg = await msg_data.msg.edit_text(text="Загрузка... ⏳")

    reports = await get_reports(
        tgid=msg_data.tgid,
        state_data=state_data,
        type_prefix=type_prefix
    )

    back_kb = IKM(inline_keyboard=[[back_current_step_btn]])

    if None in reports:
        await loading_msg.edit_text(text="Не удалось загрузить отчёт", reply_markup=back_kb)
        return

    header = await make_header(msg_data)

    text_func = text_functions[type_prefix + report_type]
    text_data = TextData(reports=reports, period=period, only_negative=only_negative)
    texts: list[str] = text_func(text_data)

    if report_type == "revenue" and recommendations:
        texts = revenue_analysis_text(text_data, msg_type="revenue_recomendations")
    
    if len(texts) == 1 and ("**" not in texts[0]): # checks if parse mode is markdown (needs rewrite)
        texts[0] = header + "\n\n" + texts[0]
    else:
        header_msg = await msg_data.msg.answer(text=header)
        await add_messages_to_delete(msg_data=msg_data, messages=[header_msg])

    for text in texts:
        if "**" in text: # checks parse mode (needs rewrite)
            parse_mode = ParseMode.MARKDOWN
        else:
            parse_mode = ParseMode.HTML
        text_msg = await msg_data.msg.answer(text=text, parse_mode=parse_mode)
        await add_messages_to_delete(msg_data=msg_data, messages=[text_msg])
    
    await msg_data.msg.answer(text="Вернуться назад?", reply_markup=back_kb)
    
    await loading_msg.delete()


async def recommendations_msg(msg_data: MsgData) -> None:
    state_data = await msg_data.state.get_data()
    
    report_type = state_data.get("report:type")
        
    if report_type == "revenue":
        await parameters_msg(msg_data, type_prefix="analysis.", only_negative=True, recommendations=True)
        return

    back_kb = IKM(inline_keyboard=[[back_current_step_btn]])
    
    text = "<b>Рекомендации 💡</b>\n" + recommendations.get(report_type)
    
    if text is None:
        await msg_data.msg.edit_text(text="Не удалось получить рекомендации", reply_markup=back_kb)
        return
    
    await msg_data.msg.edit_text(text=text, reply_markup=back_kb)
    
    