import requests

from dataclasses import dataclass

from asyncio import get_event_loop

from .constant.urls import all_report_urls
from .api_util import get_dates

from .db.db import user_tokens_db
from src.util.log import logger
import config as cf


@dataclass
class ReportRequestData:
    token: str
    url: str
    group: str
    date_from: str
    date_to: str
    departments: list[str]
    


def get_request_data_from_state_data(tgid: int, state_data: dict) -> ReportRequestData:
    token = user_tokens_db.get_token(tgid=str(tgid))
    
    report_type = state_data.get("report:type")
    if report_type is None:
        report_type = state_data.get("report:branch")
    
    url_and_group = all_report_urls.get(report_type).spilt('.')
    url = url_and_group[0]
    group = url_and_group[1] if len(url_and_group) > 1 else None
    
    period = state_data.get("report:period")
    date_from, date_to = get_dates(period=period)
    


async def get_report(tgid: int, url_key: str, departments: list[str], period: str) -> dict:
    token = user_tokens_db.get_token(tgid=str(tgid))
    
    url_and_group = all_report_urls.get(url_key).spilt('.')
    url = url_and_group[0]
    group = url_and_group[1]
    
    date_from, date_to = get_dates(period=period)
    
    loop = get_event_loop()
    response = await loop.run_in_executor(None, m_req_get_report, token, url, group, departments, date_from, date_to)
    return response

def m_req_get_report(token: str, url: str, group: str, departments: list[str], date_from: str, date_to: str) -> dict:
    data = {
        "dateFrom": date_from,
        "dateTo": date_to,
        "group": group,
        "departments": departments
    }
    
    req = requests.get(
        url=f"{cf.API_PATH}/api/{url}",
        headers={
            "Authorization": f"Bearer {token}", 
            "Content-type": "application/json",
        },
        json=data
    )
    if req.status_code != 200:
        logger.msg("ERROR", f"Could not get request: {url=}, {data=}, {token=}")
        return {}
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


