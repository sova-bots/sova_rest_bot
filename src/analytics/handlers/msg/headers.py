from aiogram.utils.formatting import Bold, Text, as_marked_section, as_key_value
from ..types.msg_data import MsgData
from ...constant.variants import all_departments, all_branches, all_types, all_periods, menu_button_translations

import logging

logger = logging.getLogger(__name__)

# make header
async def make_header(msg_data: MsgData) -> str:
    state_data = await msg_data.state.get_data()
    assert msg_data.tgid is not None, "tgid is not specified"

    headers = []

    department_id = state_data.get("report:department")
    branch_key = state_data.get("report:branch")
    report_type_key = state_data.get("report:type")
    period_key = state_data.get("report:period")
    format_type_key = state_data.get("report:format_type")

    # Логируем состояние перед обработкой
    logger.info(f"[make_header] Состояние перед обработкой: {state_data}")
    logger.info(f"[make_header] format_type_key из состояния: {format_type_key}")
    logger.info(f"[make_header] report_type_key: {report_type_key}, branch_key: {branch_key}")

    # Приводим формат к базовому виду (без show_)
    short_format_type_key = format_type_key
    if format_type_key and format_type_key.startswith("report:show_"):
        short_format_type_key = "report:" + format_type_key.split("report:show_")[1]

    # Логируем, какой ключ передаётся для перевода
    logger.info(f"[make_header] Ключ для перевода: {short_format_type_key}")

    # Переводы
    department_name = (await all_departments(msg_data.tgid)).get(department_id)
    report_type_name = all_types.get(report_type_key)
    period_name = all_periods.get(period_key)
    format_type_name = menu_button_translations.get(short_format_type_key)

    # Логируем результат перевода
    logger.info(f"[make_header] Перевод 'format_type' найден: {format_type_name}")
    logger.info(f"[make_header] Перевод для типа отчёта '{report_type_key}' найден: {report_type_name}")

    # Сбор заголовка
    if department_name:
        headers.append(f"📍 <code>Объект:</code> <b>{department_name.split('.')[-1]}</b>")

    # Используем all_types для названия отчёта
    if report_type_name:
        headers.append(f"📊 <code>Отчёт:</code> <b>{report_type_name}</b>")

    if format_type_name:
        headers.append(f"📊 <code>Форма:</code> <b>{format_type_name}</b>")
    else:
        # Если не найден перевод, добавляем сообщение
        headers.append("📊 <code>Форма:</code> <b>Не указан формат</b>")

    if period_name:
        headers.append(f"📅 <code>Период:</code> <b>{period_name}</b>")

    # Возвращаем объединённый заголовок с HTML-тегами
    return "\n".join(headers)
