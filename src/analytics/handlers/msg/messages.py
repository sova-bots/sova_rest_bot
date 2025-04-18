from aiogram.types import Message, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode

from .msg_util import clear_report_state_data, set_input_state, make_kb, make_kb_report_menu, back_current_step_btn, \
    add_messages_to_delete, subscribe_to_mailing_btn
from ..types.msg_data import MsgData
from .headers import make_header
from ...api import get_reports
from ...constant.variants import all_departments, all_branches, all_types, all_periods, all_menu_buttons
from ..text.recommendations import recommendations
from ..text.revenue_texts import revenue_analysis_text
from ..text.texts import text_functions
from ..types.text_data import TextData

from src.analytics.db.db import get_report_hint_text

# msg functions
async def department_msg(msg_data: MsgData) -> None:
    state_data = await msg_data.state.get_data()

    if state_data.get("report:step") == 0:
        await clear_report_state_data(msg_data.state)

    await set_input_state(msg_data.state, "report:department")

    assert msg_data.tgid is not None, "tgid not specified"
    departments = await all_departments(msg_data.tgid)

    header = await make_header(msg_data) + "\n\n"
    text = header + "Выберите подразделение"
    kb = make_kb(departments, back_btn=False)
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
    # стереть format_type в state
    await msg_data.state.update_data({"report:format_type": None})

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


async def parameters_msg(msg_data: MsgData, type_prefix: str = "", only_negative: bool = False,
                         recommendations: bool = False) -> None:
    state_data = await msg_data.state.get_data()

    report_type = state_data.get("report:type")
    report_format = state_data.get("report:format_type")
    period = state_data.get("report:period")

    loading_msg = await msg_data.msg.edit_text(text="Загрузка... ⏳")

    reports = await get_reports(
        tgid=msg_data.tgid,
        state_data=state_data,
        type_prefix=type_prefix
    )

    back_kb = IKM(inline_keyboard=[
        [subscribe_to_mailing_btn],
        [back_current_step_btn]
    ])

    if None in reports:
        await loading_msg.edit_text(text="Не удалось загрузить отчёт", reply_markup=back_kb)
        return

    header = await make_header(msg_data)

    text_func = text_functions[type_prefix + report_type]
    text_data = TextData(reports=reports, period=period, only_negative=only_negative)
    texts: list[str] = text_func(text_data)

    if report_type == "revenue" and recommendations:
        texts = revenue_analysis_text(text_data, recommendations=True)

    if len(texts) == 1 and ("**" not in texts[0]):
        texts[0] = header + "\n\n" + texts[0]
    else:
        header_msg = await msg_data.msg.answer(text=header)
        await add_messages_to_delete(msg_data=msg_data, messages=[header_msg])

    if not texts:
        text = "Ещё нет данных"
        text_msg = await msg_data.msg.answer(text=text, parse_mode=ParseMode.HTML)
        await add_messages_to_delete(msg_data=msg_data, messages=[text_msg])

    for text in texts:
        if "**" in text:
            parse_mode = ParseMode.MARKDOWN
        else:
            parse_mode = ParseMode.HTML
        if not text.replace("\n", ""):
            text = "Ещё нет данных"
        text_msg = await msg_data.msg.answer(text=text, parse_mode=parse_mode)
        await add_messages_to_delete(msg_data=msg_data, messages=[text_msg])

    # Добавляем подпись с ссылкой (вместо get_report_link)
    report_hint = await get_report_hint_text(msg_data.tgid, report_type, report_format)
    if report_hint:
        hint_text = f"<b>🔗 Подробнее:</b> <a href='{report_hint['url']}'>{report_hint['description']}</a>"
        hint_msg = await msg_data.msg.answer(text=hint_text, parse_mode=ParseMode.HTML)
        await add_messages_to_delete(msg_data=msg_data, messages=[hint_msg])

    await msg_data.msg.answer(text="Вернуться назад?", reply_markup=back_kb)
    await loading_msg.delete()

async def recommendations_msg(msg_data: MsgData) -> None:
    state_data = await msg_data.state.get_data()

    report_type = state_data.get("report:type")
    report_format = state_data.get("report:format_type")

    # Для выручки вызываем параметры с рекомендациями
    if report_type == "revenue":
        await msg_data.state.update_data({"showing_recommendations": True})
        await parameters_msg(msg_data, type_prefix="analysis.", only_negative=True, recommendations=True)
        await msg_data.state.update_data({"showing_recommendations": False})
        return

    # Устанавливаем флаг для отображения заголовка
    await msg_data.state.update_data({"showing_recommendations": True})
    header = await make_header(msg_data)
    await msg_data.state.update_data({"showing_recommendations": False})

    # Кнопки
    back_kb = IKM(inline_keyboard=[
        [subscribe_to_mailing_btn],
        [back_current_step_btn]
    ])

    # Рекомендации по типу
    recommendations_text = recommendations.get(report_type, "Рекомендации отсутствуют")
    text = f"{header}\n\n<b>Рекомендации 💡</b>\n{recommendations_text}"

    await msg_data.msg.edit_text(text=text, reply_markup=back_kb, parse_mode=ParseMode.HTML)

    # Подсказка/ссылка на источник
    report_hint = await get_report_hint_text(msg_data.tgid, report_type, report_format)
    if report_hint:
        hint_text = f"<b>🔗 Подробнее:</b> <a href='{report_hint['url']}'>{report_hint['description']}</a>"
        await msg_data.msg.answer(text=hint_text, parse_mode=ParseMode.HTML)

