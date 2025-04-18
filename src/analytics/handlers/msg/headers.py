from aiogram.utils.formatting import Bold, Text, as_marked_section, as_key_value
from ..types.msg_data import MsgData
from ...constant.variants import all_departments, all_branches, all_types, all_periods, menu_button_translations

import logging

logger = logging.getLogger(__name__)


async def make_header(msg_data: MsgData) -> str:
    state_data = await msg_data.state.get_data()
    assert msg_data.tgid is not None, "tgid is not specified"

    headers = []

    department_id = state_data.get("report:department")
    branch_key = state_data.get("report:branch")
    report_type_key = state_data.get("report:type")
    period_key = state_data.get("report:period")
    format_type_key = state_data.get("report:format_type")

    # Флаг показа рекомендаций
    showing_recommendations = state_data.get("showing_recommendations")

    # Логирование для отладки
    logger.info(f"[make_header] Current state data: {state_data}")
    logger.info(f"[make_header] Format type key: {format_type_key}")

    # Получаем переводы
    department_name = (await all_departments(msg_data.tgid)).get(department_id)
    report_type_name = all_types.get(report_type_key)
    period_name = all_periods.get(period_key)

    # Определяем название формата
    format_type_name = None

    # Если это рекомендации
    if showing_recommendations:
        format_type_name = "Рекомендации 💡"
    # Если формат выбран
    elif format_type_key:
        # Удаляем префикс "report:show_" если он есть
        clean_format_key = format_type_key.replace("report:show_", "")
        format_type_name = menu_button_translations.get(clean_format_key)

    # Если формат не определен
    if not format_type_name:
        format_type_name = "Не указан формат"

    # Собираем заголовок
    if department_name:
        headers.append(f"📍 <code>Объект:</code> <b>{department_name.split('.')[-1]}</b>")

    if report_type_name:
        headers.append(f"📊 <code>Отчёт:</code> <b>{report_type_name}</b>")

    headers.append(f"📊 <code>Форма:</code> <b>{format_type_name}</b>")

    if period_name:
        headers.append(f"📅 <code>Период:</code> <b>{period_name}</b>")

    logger.info(f"[make_header] Final header: {headers}")

    return "\n".join(headers)