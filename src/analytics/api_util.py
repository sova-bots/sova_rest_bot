from datetime import datetime, timedelta

from dataclasses import dataclass

from .constant.urls import all_report_urls

from .db.db import user_tokens_db
import config as cf
from src.util.log import logger


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
    
    url_and_group = all_report_urls.get(report_type).split('.')
    url = url_and_group[0]
    group = url_and_group[1] if len(url_and_group) > 1 else None
    
    departments = state_data.get("report:department")
    if departments == "all_departments":
        departments = []
    else:
        departments = [departments]
    
    period = state_data.get("report:period")
    date_from, date_to = get_dates(period=period)
    
    return ReportRequestData(token, url, group, date_from.isoformat(), date_to.isoformat(), departments)


def get_dates(period: str) -> tuple[datetime.date, datetime.date]:
    today = datetime.now(tz=cf.TIMEZONE).date()
    match period:
        case "last-day":
            date_from = today - timedelta(days=1)
            date_to = date_from
        case "this-week":
            date_from = today - timedelta(days=today.weekday())
            date_to = today
        case "this-month":
            date_from = today.replace(day=1)
            date_to = today
        case "this-year":
            date_from = today.replace(day=1, month=1)
            date_to = today
        case "last-week":
            date_from = today - timedelta(days=today.weekday()+7)
            date_to = today - timedelta(days=today.weekday()+1)
        case "last-month":
            date_from = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            date_to = today.replace(day=1) - timedelta(days=1)
        case "last-year":
            date_from = (today.replace(day=1, month=1) - timedelta(days=1)).replace(day=1, month=1)
            date_to = today.replace(day=1, month=1) - timedelta(days=1)
        case "last-last-week":
            date_from = today - timedelta(days=today.weekday()+7) - timedelta(days=7)
            date_to = today - timedelta(days=today.weekday()+1) - timedelta(days=7)
        case "last-last-month":
            date_from = ((today.replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(day=1)
            date_to = (today.replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)
        case "last-last-year":
            date_from = today.replace(day=1, month=1, year=today.year-2)
            date_to = today.replace(day=1, month=1, year=today.year-1) - timedelta(days=1)
        case _:
            logger.msg("ERROR", f"Error SendReports UnknownReportPeriod: {period=}")
            raise RuntimeError(f"Error SendReports UnknownReportPeriod: {period=}")
    return date_from, date_to




