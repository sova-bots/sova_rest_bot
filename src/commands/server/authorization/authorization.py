from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

import requests

from src.commands.server.util import db
import config as cf

router = Router(name=__name__)


@router.message(Command('server_authorize'))
async def authorize_command(msg: Message):
    await msg.answer("Command: authorize")

    loading_msg = await msg.answer("...")

    # req = requests.post(
    #     url=f"{cf.API_PATH}/api/login",
    #     data={
    #         "login": "ROGALIK",
    #         "password": "qwerty"
    #     }
    # )
    #
    # if req.status_code != 200:
    #     await loading_msg.edit_text(f"Error: {req.status_code}")
    #     return
    #
    # await loading_msg.edit_text(f"Response: {req.json()}")

    database = db.get_user_tokens_db()
    database.insert_user(
        tgid=str(msg.from_user.id),
        token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiIxIiwic2x1ZyI6IlJPR0FMSUsiLCJpYXQiOjE3MzMzMjYzNjksImV4cCI6MTczMzQxMjc2OX0.5ttqvCo7itrS5t_6Cvzp6RRiA0AyaXuWbEHY2ZgQlT4"
    )

    await loading_msg.edit_text("Response: ok")






