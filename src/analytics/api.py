import requests

from asyncio import get_event_loop

from .db.db import user_tokens_db
from util.log import logger
import config as cf


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

