import logging
import re

from aiogram import Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from .msg_util import (
    clear_report_state_data, set_input_state, make_kb, make_kb_report_menu,
    back_current_step_btn, add_messages_to_delete, subscribe_to_mailing_btn
)
from ..types.msg_data import MsgData
from .headers import make_header
from ...api import get_reports
from ...constant.variants import all_departments, all_branches, all_types, all_periods, all_menu_buttons
from ..text.recommendations import recommendations
from ..text.revenue_texts import revenue_analysis_text, revenue_recommendations
from ..text.texts import text_functions
from ..types.text_data import TextData
from src.mailing.commands.registration.notifications.sub_mail import SubscriptionState

logger = logging.getLogger(__name__)

menu_router = Router()


async def check_state_data(state):
    data = await state.get_data()
    logging.info(f"State data: {data}")


# == Этапы выбора ==

async def department_msg(msg_data: MsgData) -> None:
    state_data = await msg_data.state.get_data()
    if state_data.get("report:step") == 0:
        await clear_report_state_data(msg_data.state)

    await set_input_state(msg_data.state, "report:department")

    departments = await all_departments(msg_data.tgid)
    text = "Выберите подразделение"
    kb = make_kb(departments)
    await msg_data.msg.edit_text(text=text, reply_markup=kb)

    await check_state_data(msg_data.state)


async def branch_msg(msg_data: MsgData) -> None:
    await set_input_state(msg_data.state, "report:branch")

    text = "Укажите вид отчёта"
    kb = make_kb(all_branches)
    await msg_data.msg.edit_text(text=text, reply_markup=kb)

    await check_state_data(msg_data.state)


async def type_msg(msg_data: MsgData, type_indexes: list[int]) -> None:
    await set_input_state(msg_data.state, "report:type")

    text = "Выберите тип отчета"
    kb = make_kb(all_types, type_indexes)
    await msg_data.msg.edit_text(text=text, reply_markup=kb)

    if type_indexes and type_indexes[0] in all_types:
        selected_type = all_types[type_indexes[0]]
        await msg_data.state.update_data(report_type=selected_type)
        logging.info(f"Пользователь {msg_data.tgid} выбрал тип отчета: {selected_type}")
    else:
        logging.error(f"Неверный индекс типа отчета: {type_indexes}")
        return

    await msg_data.state.set_state(SubscriptionState.choosing_period)
    await msg_data.msg.answer("Теперь выберите период данных для отчета.")


async def period_msg(msg_data: MsgData, period_indexes: list[int]) -> None:
    await set_input_state(msg_data.state, "report:period")

    text = "Выберите срок отчёта:"
    kb = make_kb(all_periods, period_indexes)
    await msg_data.msg.edit_text(text=text, reply_markup=kb)

    await check_state_data(msg_data.state)


# Обновляем форматирование для заголовков и данных:
async def menu_msg(msg_data: MsgData, buttons_indexes: list[int]) -> None:
    # 1. Получаем выбранную кнопку
    button = all_menu_buttons[buttons_indexes[0]]
    # 2. Сохраняем её в state
    await msg_data.state.update_data({"report:format_type": button.callback_data})

    # 3. Только после этого вызываем make_header — теперь в state уже есть report:format_type
    header = await make_header(msg_data) + "\n\n"
    text = header + "Выберите"
    kb = make_kb_report_menu(all_menu_buttons, buttons_indexes)

    # Проверяем, что формат корректный
    if re.search(r"<(b|code)>", text):
        parse_mode = ParseMode.HTML
    else:
        parse_mode = ParseMode.MARKDOWN

    await msg_data.msg.edit_text(text=text, reply_markup=kb, parse_mode=parse_mode)


async def parameters_msg(msg_data: MsgData, type_prefix: str = "", only_negative: bool = False,
                         recommendations: bool = False) -> None:
    state_data = await msg_data.state.get_data()
    logger.info(f"[parameters_msg] Состояние до обновления: {state_data}")

    report_type = state_data.get("report:type")
    period = state_data.get("report:period")

    if not state_data.get("report:format_type"):
        new_format_type = f"report:{type_prefix or 'parameters'}"
        await msg_data.state.update_data({"report:format_type": new_format_type})
        logger.info(f"[parameters_msg] Установлен report:format_type -> {new_format_type}")

    state_data = await msg_data.state.get_data()
    logger.info(f"[parameters_msg] Состояние после обновления: {state_data}")

    loading_msg = await msg_data.msg.edit_text(text="Загрузка... ⏳")

    reports = await get_reports(tgid=msg_data.tgid, state_data=state_data, type_prefix=type_prefix)
    back_kb = IKM(inline_keyboard=[[subscribe_to_mailing_btn], [back_current_step_btn]])

    if None in reports:
        logger.warning(f"[parameters_msg] Один из отчётов не загружен: {reports}")
        await loading_msg.edit_text(text="Не удалось загрузить отчёт", reply_markup=back_kb)
        return

    header = await make_header(msg_data)
    text_func = text_functions[type_prefix + report_type]
    text_data = TextData(reports=reports, period=period, only_negative=only_negative)

    if report_type == "revenue" and recommendations:
        texts = revenue_analysis_text(text_data)
    else:
        texts = text_func(text_data)

    for i, text in enumerate(texts):
        # Оставляем ParseMode.HTML по умолчанию, если хотите, чтобы всегда использовался HTML
        parse_mode = ParseMode.HTML  # или ParseMode.MARKDOWN, если хотите использовать Markdown для определённых случаев

        full_text = f"{header}\n\n{text}" if i == 0 and not re.search(r"(📍|<code>Объект:|<b>Объект:)", text) else text
        text_msg = await msg_data.msg.answer(text=full_text, parse_mode=parse_mode)
        await add_messages_to_delete(msg_data=msg_data, messages=[text_msg])

    await msg_data.msg.answer(text="Вернуться назад?", reply_markup=back_kb)
    await loading_msg.delete()


async def recommendations_msg(msg_data: MsgData) -> None:
    state_data = await msg_data.state.get_data()
    logger.info(f"[recommendations_msg] Состояние до обновления: {state_data}")

    report_type = state_data.get("report:type")

    if not state_data.get("report:format_type"):
        await msg_data.state.update_data({"report:format_type": "report:recommendations"})
        logger.info(f"[recommendations_msg] Установлен report:format_type -> report:recommendations")

    state_data = await msg_data.state.get_data()
    logger.info(f"[recommendations_msg] Состояние после обновления: {state_data}")

    header = await make_header(msg_data)
    back_kb = IKM(inline_keyboard=[[subscribe_to_mailing_btn], [back_current_step_btn]])

    if report_type == "revenue":
        if revenue_recommendations:
            combined_text = "\n\n".join(revenue_recommendations.values())
            content = f"<b>Рекомендации по выручке 💡</b>\n\n{combined_text}"
        else:
            logger.warning("[recommendations_msg] Не удалось получить рекомендации по выручке.")
            content = "Не удалось получить рекомендации по выручке."
    else:
        recommendation_text = recommendations.get(report_type)
        content = f"<b>Рекомендации 💡</b>\n{recommendation_text}" if recommendation_text else "Не удалось получить рекомендации."

    final_text = content if any(tag in content for tag in ["📍", "<b>", "<code>"]) else f"{header}\n\n{content}"

    await msg_data.msg.edit_text(text=final_text, reply_markup=back_kb, parse_mode=ParseMode.HTML)
