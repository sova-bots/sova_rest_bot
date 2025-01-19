from aiogram.fsm.context import FSMContext

from ..properties import revenue_properties, revenue_dynamics
from ..report_util import get_department_name, report_types, report_periods, get_report_parameters_from_state


def str_if_exists(name, value, properties, is_dynamic: bool) -> str:
    if name not in properties.keys() or value is None:
        return ""
    
    if is_dynamic:
        if value > 0:
            sign = "+"
        else:
            sign = ""
        return f"<b>{properties[name]}:</b> {sign}{value:,.0f}% \n"
    
    return f"<b>{properties[name]}:</b> {value:,.0f} \n"


def str_head(r: dict, report_type, report_period) -> str:
    return f"""
Объект: <b>{r["label"]}</b>
Отчёт: <b>{report_types[report_type]}</b>
Период: <b>{report_periods[report_period]}</b>
{report_types[report_type]} за <b>{report_periods[report_period]}</b>
"""


async def make_text(r: dict, state: FSMContext) -> str:

    report_type, report_departments, report_period = await get_report_parameters_from_state(state)

    text = str_head(r, report_type, report_period)
    text += "\n<i>Показатели</i>\n\n"

    for k, v in r.items():
        text += str_if_exists(k, v, revenue_properties, False)

    text += '\n'

    for k, v in r.items():
        text += str_if_exists(k, v, revenue_dynamics, True)

    return text