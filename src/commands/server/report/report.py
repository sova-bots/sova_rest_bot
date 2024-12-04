from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

import requests

from src.commands.server.util import db
import config as cf

router = Router(name=__name__)


async def send_request_to_get_reports(token: str):
    req = requests.post(
        url=f"{cf.API_PATH}/api/revenue",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "dateFrom": "2024-11-04",
            "dateTo": "2024-11-11"
        }
    )
    return req


@router.message(Command('server_get_report'))
async def get_report(msg: Message):
    database = db.get_user_tokens_db()
    token = database.get_token(tgid=str(msg.from_user.id))

    loading_msg = await msg.answer("...")

    req = await send_request_to_get_reports(token)

    if req.status_code != 200:
        await loading_msg.edit_text(f"Error: {req.status_code}")
        return

    text = ""
    for rep in req.json()['report']:
        text += f"\n{rep}\n"

    await loading_msg.edit_text(text)

