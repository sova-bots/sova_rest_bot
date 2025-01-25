from aiogram.fsm.context import FSMContext

from ..report_util import get_department_name, report_types, report_periods, get_report_parameters_from_state



def str_if_exists(name, value, properties, is_dynamic: bool) -> str:
    if name not in properties.keys() or value is None:
        return ""
    
    if is_dynamic:
        if value > 0:
            sign = "+"
        else:
            sign = ""
        return f"<b>{properties[name][0]}:</b> {sign}{value:,.0f} % \n"
    
    return f"<b>{properties[name][0]}:</b> {value:,.0f} {properties[name][1]} \n"


def str_head(r: dict, report_type, report_period) -> str:
    return f"""
Объект: <b>{r["label"]}</b>
Отчёт: <b>{report_types[report_type]}</b>
Период: <b>{report_periods[report_period]}</b>
{report_types[report_type]} за <b>{report_periods[report_period]}</b>
"""


async def make_text(r: dict, properties: dict, state: FSMContext) -> str:

    report_type, report_departments, report_period = await get_report_parameters_from_state(state)

    text = str_head(r, report_type, report_period)
    text += "\n<i>Показатели</i>\n\n"

    for prop_type, props in properties.items():
        for k, v in r.items():
            is_dynamic = prop_type == "dynamics"
            text += str_if_exists(k, v, props, is_dynamic)
        text += '\n'

    return text