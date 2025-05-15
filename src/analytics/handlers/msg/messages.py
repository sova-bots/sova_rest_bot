import json

from aiogram.types import Message, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode

import asyncio

from .msg_util import clear_report_state_data, set_input_state, make_kb, make_kb_report_menu, back_current_step_btn, \
    add_messages_to_delete, send_file_buttons_kb
from ..types.msg_data import MsgData
from .headers import make_header, make_header_from_state
from ...api import get_reports, get_reports_from_state, get_departments

from ..types.report_all_departments_types import ReportAllDepartmentTypes
from aiogram.types import Message, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from src.util.log import logger
from urllib.parse import unquote


from aiogram.enums.parse_mode import ParseMode
from .msg_util import clear_report_state_data, set_input_state, make_kb, make_kb_report_menu, back_current_step_btn, \
    add_messages_to_delete, subscribe_to_mailing_btn, send_pdf_report_btn, send_excel_report_btn
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


async def parameters_msg(
        msg_data: MsgData,
        type_prefix: str = "",
        only_negative: bool = False,
        recommendations: bool = False
) -> None:
    state_data = await msg_data.state.get_data()

    report_format = state_data.get("report:format_type")
    report_type = state_data.get("report:type")
    department = state_data.get("report:department")
    period = state_data.get("report:period")

    loading_msg = await msg_data.msg.edit_text(text="Загрузка... ⏳")
    back_kb = IKM(inline_keyboard=[[back_current_step_btn]])

    # Если "один объект" или "вся сеть (итого)"
    if department != ReportAllDepartmentTypes.ALL_DEPARTMENTS_INDIVIDUALLY:
        reports = await get_reports_from_state(
            tgid=msg_data.tgid,
            state_data=state_data,
            type_prefix=type_prefix,
        )

        if None in reports:
            await loading_msg.edit_text(text="Не удалось загрузить отчёт", reply_markup=back_kb)
            return

        header = await make_header(msg_data)
        await send_one_texts(
            reports, msg_data, report_type, type_prefix, period, department,
            only_negative, recommendations, header=header, aggregated=False
        )

    else:  # Если "вся сеть (по объектам отдельно)"
        copied_state_data = state_data.copy()
        department_reports = []

        for dep_id, dep_name in (await get_departments(msg_data.tgid)).items():
            copied_state_data["report:department"] = dep_id
            reports = await get_reports_from_state(
                tgid=msg_data.tgid,
                state_data=copied_state_data,
                type_prefix=type_prefix,
            )

            if None in reports:
                await loading_msg.edit_text(text="Не удалось загрузить отчёт", reply_markup=back_kb)
                return

            header = await make_header_from_state(copied_state_data, msg_data.tgid)
            department_reports.append({"reports": reports, "header": header})

        header_text = (await make_header(msg_data)) + "\n\n⬇️⬇️⬇️"
        header_msg = await msg_data.msg.answer(text=header_text)
        await add_messages_to_delete(msg_data=msg_data, messages=[header_msg])

        # Отправляем данные по каждому отделу без ссылок и меню
        for department_report in department_reports:
            await send_one_texts(
                department_report["reports"],
                msg_data,
                report_type,
                type_prefix,
                period,
                department,
                only_negative,
                recommendations,
                header=department_report["header"],
                aggregated=True  # В агрегированном режиме
            )

        # # После цикла отправляем один раз ссылки (подсказку), если они есть
        # report_hint = await get_report_hint_text(msg_data.tgid, report_type, report_format)
        # if report_hint:
        #     # Если ссылка содержит несколько URL (разделённых символом переноса строки или другим разделителем)
        #     urls = [url.strip() for url in report_hint["url"].split("\n") if url.strip()]
        #     if urls:
        #         # Отправляем заголовок ссылки
        #         hint_header = await msg_data.msg.answer(
        #             text=f"<b>🔗 {report_hint['description']}:</b>",
        #             parse_mode=ParseMode.HTML
        #         )
        #         await add_messages_to_delete(msg_data=msg_data, messages=[hint_header])
        #         # Отправляем первую ссылку (либо можно объединить все в одно сообщение, если требуется)
        #         hint_msg = await msg_data.msg.answer(
        #             text=f"1. <a href='{urls[0]}'>Материал</a>",
        #             parse_mode=ParseMode.HTML,
        #             disable_web_page_preview=True
        #         )
        #         await add_messages_to_delete(msg_data=msg_data, messages=[hint_msg])

        # Отправляем единое меню для всех отделов
        aggregated_kb = IKM(inline_keyboard=[
            [subscribe_to_mailing_btn],
            *send_file_buttons_kb.inline_keyboard,
            [back_current_step_btn]
        ])
        await msg_data.msg.answer(text="Что дальше?", reply_markup=aggregated_kb)

    await loading_msg.delete()


async def send_one_texts(
        reports: list[dict],
        msg_data: MsgData,
        report_type: str,
        type_prefix: str,
        period: str,
        department: str,
        only_negative: bool,
        recommendations: bool,
        header: str = "",
        aggregated: bool = False  # Новый параметр
) -> None:
    state_data = await msg_data.state.get_data()
    report_format = state_data.get("report:format_type")
    period = state_data.get("report:period")

    text_func = text_functions[type_prefix + report_type]
    text_data = TextData(reports=reports, period=period, department=department, only_negative=only_negative)
    texts: list[str] = text_func(text_data)

    if report_type == "revenue" and recommendations:
        texts = revenue_analysis_text(text_data, recommendations=True)

    # Отправка основного контента
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
        parse_mode = ParseMode.MARKDOWN if "**" in text else ParseMode.HTML
        if not text.strip():
            text = "Ещё нет данных"
        text_msg = await msg_data.msg.answer(text=text, parse_mode=parse_mode)
        await add_messages_to_delete(msg_data=msg_data, messages=[text_msg])

    # Отправка ссылок с подробностями (подсказок) – выполняется, только если не агрегируем
    if not aggregated:
        report_hint = await get_report_hint_text(msg_data.tgid, report_type, report_format)
        if report_hint:
            urls = report_hint["url"].split("\n")
            for url in urls:
                url = url.strip()
                if url:
                    hint_text = f"<b>🔗 Подробнее:</b> <a href='{url}'>{report_hint['description']}</a>"
                    hint_msg = await msg_data.msg.answer(text=hint_text, parse_mode=ParseMode.HTML)
                    await add_messages_to_delete(msg_data=msg_data, messages=[hint_msg])

        back_kb = IKM(inline_keyboard=[
            [subscribe_to_mailing_btn],
            *send_file_buttons_kb.inline_keyboard,
            [back_current_step_btn]
        ])
        await msg_data.msg.answer(text="Что дальше?", reply_markup=back_kb)
        await msg_data.state.update_data({"report:json_data": reports})


async def recommendations_msg(msg_data: MsgData) -> None:
    state_data = await msg_data.state.get_data()
    report_format = state_data.get("report:format_type")
    period = state_data.get("report:period")
    report_type = state_data.get("report:type")

    # Получаем шапку отчёта
    header = await make_header(msg_data)

    # Клавиатура
    back_kb = IKM(inline_keyboard=[
        [subscribe_to_mailing_btn],
        *send_file_buttons_kb.inline_keyboard,
        [back_current_step_btn]
    ])

    # Специальный случай для выручки
    if report_type == "revenue":
        await parameters_msg(msg_data, type_prefix="analysis.", only_negative=True, recommendations=True)
        return

    # Основной текст рекомендаций
    text = recommendations.get(report_type)
    if text is None:
        await msg_data.msg.edit_text(text="Не удалось получить рекомендации", reply_markup=back_kb)
        return

    # Дополнительные ссылки
    hint_texts = []
    report_hint = await get_report_hint_text(msg_data.tgid, report_type, report_format)
    if report_hint:
        urls = report_hint["url"].split("\n")
        for url in urls:
            url = url.strip()
            if url:
                hint_texts.append(f"<b>🔗 Подробнее:</b> <a href='{url}'>{report_hint['description']}</a>")

        logger.info(
            f"[report_hint] tgid={msg_data.tgid}, report_type={report_type}, report_format={report_format}, hint={report_hint}")

    # Собираем итоговый текст
    full_text = header + "\n" + text
    if hint_texts:
        full_text += "\n\n" + "\n".join(hint_texts)

    # Отправляем единое сообщение с одной клавиатурой
    await msg_data.msg.edit_text(text=full_text, reply_markup=back_kb, parse_mode=ParseMode.HTML)



