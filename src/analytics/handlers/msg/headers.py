from aiogram.utils.formatting import Bold, Text, as_marked_section, as_key_value

from ..types.msg_data import MsgData
from ...constant.variants import all_departments, all_branches, all_types, all_periods

# make header
async def make_header(msg_data: MsgData) -> str:
    state_data = await msg_data.state.get_data()
    
    headers = []
    
    department = state_data.get("report:department")
    branch = state_data.get("report:branch")
    report_type = state_data.get("report:type")
    period = state_data.get("report:period")
    
    assert msg_data.tgid is not None, "tgid is not specified"
    
    department = (await all_departments(msg_data.tgid)).get(department)
    branch = all_branches.get(branch)
    report_type = all_types.get(report_type)
    period = all_periods.get(period)
    
    if department is not None:
        headers.append(f"<code>Объект:</code> <b>{department.split('.')[-1]}</b>")
        
    if report_type is None and branch is not None:
        headers.append(f"<code>Отчёт:</code> <b>{branch}</b>")
        
    if report_type is not None:
        headers.append(f"<code>Отчёт:</code> <b>{report_type}</b>")
        
    if period is not None:
        headers.append(f"<code>Период:</code> <b>{period}<b>")
        
    return "\n".join(headers)
    
    
    
    
    