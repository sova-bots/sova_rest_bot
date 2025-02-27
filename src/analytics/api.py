import requests

from asyncio import get_event_loop

from .api_util import get_dates, get_request_data_from_state_data, ReportRequestData

from .db.db import user_tokens_db
from src.util.log import logger
import config as cf


async def get_report(tgid: int, state_data: dict) -> dict | None:
    request_data = get_request_data_from_state_data(tgid, state_data)
    loop = get_event_loop()
    response = await loop.run_in_executor(None, m_req_get_report, request_data.token, request_data.url, request_data.group, request_data.departments, request_data.date_from, request_data.date_to)
    return response

def m_req_get_report(token: str, url: str, group: str, departments: list[str], date_from: str, date_to: str) -> dict | None:
    data = {
        "dateFrom": date_from,
        "dateTo": date_to,
        "group": group,
        "departments": departments
    }
    
    logger.debug(f"SendRequest: {url=}, {data=}, {token=}")
    
    req = requests.post(
        url=f"{cf.API_PATH}/api/{url}",
        headers={
            "Authorization": f"Bearer {token}", 
            "Content-type": "application/json",
        },
        json=data
    )
    
    logger.debug(f"ResievedResponse: {req.text}, status={req.status_code}; request: {url=}, {data=}, {token=}")
    
    if req.status_code != 200:
        logger.msg("ERROR", f"Could not get request: {url=}, {data=}, {token=}")
        return None
    return req.json()


async def get_departments(tgid: int) -> dict:
    token = user_tokens_db.get_token(tgid=str(tgid))
    loop = get_event_loop()
    departments = await loop.run_in_executor(None, m_req_get_departments, token)
    departments_remapped = { dep["id"]: dep["name"] for dep in departments }
    return departments_remapped

def m_req_get_departments(token: str) -> dict:
    req = requests.get(
        url=f"{cf.API_PATH}/api/departments",
        headers={"Authorization": f"Bearer {token}"},
    )
    if req.status_code != 200:
        logger.msg("ERROR", f"Could not get departments: {token=}")
        return []
    return req.json()['departments'] + [{"id": "all_departments", "name": "Вся сеть"}]


