from .msg_util import clear_report_state_data, set_input_state, make_kb, make_kb_report_menu, back_current_step_btn, \
    add_messages_to_delete, send_file_buttons_kb, back_to_main_menu_btn, back_previous_step_btn
from .headers import make_header_from_state
from ...api import get_reports_from_state, get_departments

from ..types.report_all_departments_types import ReportAllDepartmentTypes
from aiogram.types import Message, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from src.util.log import logger

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

    null_btn = IKB(text=" ", callback_data="ignore")

    # Добавляем нижний ряд: [null_btn, back_previous_step_btn, null_btn]
    kb.inline_keyboard.append([null_btn, back_previous_step_btn, null_btn])

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


async def send_aggregated_menu_once(msg_data: MsgData) -> None:
    kb = IKM(inline_keyboard=[
        [subscribe_to_mailing_btn],
        *send_file_buttons_kb.inline_keyboard,
        [back_current_step_btn]
    ])
    menu_msg = await msg_data.msg.answer(text="Что дальше?", reply_markup=kb)
    await add_messages_to_delete(msg_data=msg_data, messages=[menu_msg])


async def send_report_hint_once(msg_data: MsgData, report_type: str, report_format: str) -> None:
    report_hint = await get_report_hint_text(msg_data.tgid, report_type, report_format)
    if not report_hint:
        return

    urls = [url.strip() for url in report_hint["url"].split("\n") if url.strip()]
    if not urls:
        return

    hint_header = await msg_data.msg.answer(
        text=f"<b>🔗 {report_hint['description']}:</b>",
        parse_mode=ParseMode.HTML
    )
    await add_messages_to_delete(msg_data=msg_data, messages=[hint_header])

    hint_msg = await msg_data.msg.answer(
        text=f"<a href='{urls[0]}'>Перейти к отчёту</a>",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )
    await add_messages_to_delete(msg_data=msg_data, messages=[hint_msg])


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
        aggregated: bool = False
) -> None:
    state_data = await msg_data.state.get_data()
    report_format = state_data.get("report:format_type")
    period = state_data.get("report:period")

    text_func = text_functions[type_prefix + report_type]
    text_data = TextData(reports=reports, period=period, department=department, only_negative=only_negative)
    texts: list[str] = text_func(text_data)

    if report_type == "revenue" and recommendations:
        texts = revenue_analysis_text(text_data, recommendations=True)

    # Отправка заголовка, если нужен
    if len(texts) == 1 and ("**" not in texts[0]):
        texts[0] = header + "\n\n" + texts[0]
    else:
        header_msg = await msg_data.msg.answer(text=header)
        await add_messages_to_delete(msg_data=msg_data, messages=[header_msg])

    # Отправка текста, если он есть
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

    # Для агрегированных отчетов (все департаменты) показываем меню и подсказки только один раз в конце
    if not aggregated:
        # Для отдельных департаментов показываем подсказки и меню сразу
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
        menu_msg = await msg_data.msg.answer(text="Что дальше?", reply_markup=back_kb)
        await add_messages_to_delete(msg_data=msg_data, messages=[menu_msg])

    # Сохраняем данные в state в любом случае
    await msg_data.state.update_data({"report:json_data": reports})


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

    loading_msg = await msg_data.msg.answer(text="Загрузка... ⏳")
    await add_messages_to_delete(msg_data=msg_data, messages=[loading_msg])

    back_kb = IKM(inline_keyboard=[[back_current_step_btn]])

    if department != ReportAllDepartmentTypes.ALL_DEPARTMENTS_INDIVIDUALLY:
        reports = await get_reports_from_state(
            tgid=msg_data.tgid,
            state_data=state_data,
            type_prefix=type_prefix,
        )

        if None in reports:
            await loading_msg.edit_text(text="Не удалось загрузить отчёт", reply_markup=back_kb)
            return

        await loading_msg.delete()
        header = await make_header_from_state(state_data, msg_data.tgid)

        await send_one_texts(
            reports=reports,
            msg_data=msg_data,
            report_type=report_type,
            type_prefix=type_prefix,
            period=period,
            department=department,
            only_negative=only_negative,
            recommendations=recommendations,
            header=header,
            aggregated=False
        )

    else:
        departments = await get_departments(msg_data.tgid)
        if not departments:
            await loading_msg.edit_text(text="Нет доступных подразделений", reply_markup=back_kb)
            return

        await loading_msg.delete()

        for dep_id, dep_name in departments.items():
            await msg_data.state.update_data({"report:department": dep_id})
            state_data = await msg_data.state.get_data()

            reports = await get_reports_from_state(
                tgid=msg_data.tgid,
                state_data=state_data,
                type_prefix=type_prefix,
            )

            if None in reports:
                text_msg = await msg_data.msg.answer(
                    text=f"⚠️ Не удалось загрузить отчёт по подразделению: {dep_name}",
                    parse_mode=ParseMode.HTML
                )
                await add_messages_to_delete(msg_data=msg_data, messages=[text_msg])
                continue

            header = await make_header_from_state(state_data, msg_data.tgid)

            await send_one_texts(
                reports=reports,
                msg_data=msg_data,
                report_type=report_type,
                type_prefix=type_prefix,
                period=period,
                department=dep_id,
                only_negative=only_negative,
                recommendations=recommendations,
                header=header,
                aggregated=True
            )

        # После всех подразделений — ОДИН раз показываем подсказки и меню
        await msg_data.state.update_data({"report:department": ReportAllDepartmentTypes.ALL_DEPARTMENTS_INDIVIDUALLY})
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
        menu_msg = await msg_data.msg.answer(text="Что дальше?", reply_markup=back_kb)
        await add_messages_to_delete(msg_data=msg_data, messages=[menu_msg])


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

    loading_msg = await msg_data.msg.answer(text="Загрузка... ⏳")
    await add_messages_to_delete(msg_data=msg_data, messages=[loading_msg])

    back_kb = IKM(inline_keyboard=[[back_current_step_btn]])

    # Обычный отчёт, не по всем департаментам
    if department != ReportAllDepartmentTypes.ALL_DEPARTMENTS_INDIVIDUALLY:
        reports = await get_reports_from_state(
            tgid=msg_data.tgid,
            state_data=state_data,
            type_prefix=type_prefix,
        )

        # Проверка: пустой список или ошибка получения отчета
        if not reports or any(report is None for report in reports):
            await loading_msg.edit_text(text="Не удалось загрузить отчёт", reply_markup=back_kb)
            return

        await loading_msg.delete()
        header = await make_header_from_state(state_data, msg_data.tgid)

        await send_one_texts(
            reports=reports,
            msg_data=msg_data,
            report_type=report_type,
            type_prefix=type_prefix,
            period=period,
            department=department,
            only_negative=only_negative,
            recommendations=recommendations,
            header=header,
            aggregated=False
        )

    # Отчёт по всем департаментам (агрегированный)
    else:
        departments = await get_departments(msg_data.tgid)
        if not departments:
            await loading_msg.edit_text(text="Нет доступных подразделений", reply_markup=back_kb)
            return

        await loading_msg.delete()

        # Собираем и отображаем отчёты для каждого департамента отдельно
        for dep_id, dep_name in departments.items():
            try:
                temp_state = state_data.copy()
                temp_state["report:department"] = dep_id

                reports = await get_reports_from_state(
                    tgid=msg_data.tgid,
                    state_data=temp_state,
                    type_prefix=type_prefix,
                )

                # Пропускаем, если отчёта нет или он пустой
                if not reports or any(report is None for report in reports):
                    continue

                header = await make_header_from_state(temp_state, msg_data.tgid)

                await send_one_texts(
                    reports=reports,
                    msg_data=msg_data,
                    report_type=report_type,
                    type_prefix=type_prefix,
                    period=period,
                    department=dep_id,
                    only_negative=only_negative,
                    recommendations=recommendations,
                    header=header,
                    aggregated=True  # <- aggregated=True, чтобы меню и ссылки не дублировались
                )

            except Exception as e:
                logger.error(f"Ошибка при обработке департамента {dep_id}: {e}")
                continue

        # В конце выводим общее меню и подсказки один раз
        await send_report_hint_once(msg_data, report_type, report_format)
        await send_aggregated_menu_once(msg_data)

    # Сохраняем json-данные в состояние, если нужен экспорт
    # (например, последний отчёт может быть полезен для отправки Excel)
    await msg_data.state.update_data({"report:json_data": reports})



async def recommendations_msg(msg_data: MsgData) -> None:
    state_data = await msg_data.state.get_data()
    report_format = state_data.get("report:format_type")
    period = state_data.get("report:period")
    report_type = state_data.get("report:type")
    departments = state_data.get("report:departments")  # <-- добавим это, если ещё не было

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
        await msg_data.msg.edit_text(
            text="Не удалось получить рекомендации",
            reply_markup=back_kb
        )
        return

    # --- Обработка ссылки-подсказки (report_hint) ---
    full_hint_block = ""
    if departments == "all_departments":
        # Только одна ссылка
        report_hint = await get_report_hint_text(msg_data.tgid, report_type, report_format)
        if report_hint:
            url = report_hint["url"].strip().split("\n")[0]  # первая строка
            description = report_hint["description"]
            full_hint_block = f"\n\n<b>🔗 Подробнее:</b> <a href='{url}'>{description}</a>"

            logger.info(
                f"[report_hint:ALL] tgid={msg_data.tgid}, report_type={report_type}, report_format={report_format}, hint={report_hint}"
            )
    else:
        # Могут быть несколько ссылок
        report_hint = await get_report_hint_text(msg_data.tgid, report_type, report_format)
        if report_hint:
            urls = report_hint["url"].split("\n")
            hint_texts = []
            for url in urls:
                url = url.strip()
                if url:
                    hint_texts.append(f"<b>🔗 Подробнее:</b> <a href='{url}'>{report_hint['description']}</a>")
            full_hint_block = "\n\n" + "\n".join(hint_texts)

            logger.info(
                f"[report_hint:MULTI] tgid={msg_data.tgid}, report_type={report_type}, report_format={report_format}, hint={report_hint}"
            )

    # Финальный текст
    full_text = header + "\n" + text + full_hint_block

    await msg_data.msg.edit_text(
        text=full_text,
        reply_markup=back_kb,
        parse_mode=ParseMode.HTML
    )



