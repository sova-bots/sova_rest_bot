import requests

from asyncio import get_event_loop

from .api_util import get_dates

from .db.db import user_tokens_db, get_access_list_data
from src.util.log import logger
import config as cf

from dataclasses import dataclass

from .constant.urls import all_report_urls
from .handlers.types.report_all_departments_types import ReportAllDepartmentTypes


@dataclass
class ReportRequestData:
    token: str
    url: str
    group: str
    date_from: str
    date_to: str
    departments: list[str]


async def get_requests_datas_from_state_data(tgid: int, state_data: dict, type_prefix: str) -> list[ReportRequestData]:
    token = user_tokens_db.get_token(tgid=str(tgid))

    report_type = state_data.get("report:type", "null")

    url_list = all_report_urls.get(type_prefix + report_type)
    if url_list is None:
        raise RuntimeError("No url. Please specify url for \"{report_type}\" report type in urls.py")

    result = []

    for url in url_list:
        url_and_group = url.split('.')

        url = url_and_group[0]
        group = url_and_group[1] if len(url_and_group) > 1 else None

        departments_data = await get_departments(tgid)

        departments = state_data.get("report:department")
        if departments in [ReportAllDepartmentTypes.ALL_DEPARTMENTS_INDIVIDUALLY,
                           ReportAllDepartmentTypes.SUM_DEPARTMENTS_TOTALLY]:
            departments = list(departments_data.keys())
        else:
            departments = [departments]

        period = state_data.get("report:period")
        date_from, date_to = get_dates(period=period)

        data = ReportRequestData(token, url, group, date_from.isoformat(), date_to.isoformat(), departments)
        result.append(data)
    return result


async def get_reports_from_state(tgid: int, state_data: dict, type_prefix: str) -> list[dict] | None:
    request_data_list = await get_requests_datas_from_state_data(tgid, state_data, type_prefix)
    return await get_reports(request_data_list)


async def get_reports(request_data_list: list[ReportRequestData]) -> list[dict] | None:
    responses = []
    for request_data in request_data_list:
        loop = get_event_loop()
        response = await loop.run_in_executor(None, m_req_get_report, request_data.token, request_data.url,
                                              request_data.group, request_data.departments, request_data.date_from,
                                              request_data.date_to)
        responses.append(response)
    return responses


def m_req_get_report(token: str, url: str, group: str, departments: list[str], date_from: str,
                     date_to: str) -> dict | None:
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


async def get_departments(tgid: int, stop_list: list[str] = [], access_data: dict | None = None) -> dict:
    token = user_tokens_db.get_token(tgid=str(tgid))
    loop = get_event_loop()
    departments = await loop.run_in_executor(None, m_req_get_departments, token)
    departments_remapped = {dep["id"]: dep["name"] for dep in departments}

    # стоп лист
    for id_ in stop_list:
        removed = departments_remapped.pop(id_, None)  # если не найдёт id_ в ключах departments_remapped, то вернёт None

    # получение пропускного листа
    if access_data is None:
        access_data = await get_access_list_data()

    # пропускной лист
    if tgid not in access_data.keys():
        return {}
    departments_result = {}

    for department_id, department_name in departments_remapped.items():
        if department_id in access_data[tgid]:
            departments_result[department_id] = department_name

    return departments_result


def m_req_get_departments(token: str) -> dict:
    req = requests.get(
        url=f"{cf.API_PATH}/api/departments",
        headers={"Authorization": f"Bearer {token}"},
    )
    if req.status_code != 200:
        logger.msg("ERROR", f"Could not get departments: {token=}")
        return {}
    return req.json()['departments']
