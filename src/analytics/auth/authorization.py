import requests
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.types import Message

import config as cf
from src.analytics.db.db import user_tokens_db
from src.util.log import logger

router = Router(name=__name__)


class FSMReportAuthorization(StatesGroup):
    ask_login = State()
    ask_password = State()


@router.callback_query(F.data == "server_report_reauth")
async def reauthorization_handler(query: CallbackQuery, state: FSMContext):
    user_tokens_db.delete_user(tgid=str(query.from_user.id))
    await server_report_authorize_cq_handler(query, state)


@router.callback_query(F.data == "server_report_authorization")
async def server_report_authorize_cq_handler(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.answer("<b>Сначала необходимо авторизироваться в систему</b>\n\nВведите логин")
    await state.set_state(FSMReportAuthorization.ask_login)
    await query.answer()


@router.message(FSMReportAuthorization.ask_login)
async def ask_password(message: Message, state: FSMContext):
    if not message.text:
        return

    await state.update_data({'server_report_login': message.text})

    await message.answer("Введите пароль")
    await state.set_state(FSMReportAuthorization.ask_password)


@router.message(FSMReportAuthorization.ask_password)
async def authorize(message: Message, state: FSMContext):
    if not message.text:
        return

    user_id = message.from_user.id
    login = (await state.get_data()).get('server_report_login')
    password = message.text

    msg = await message.answer("Загрузка... ⚙️")

    req = requests.post(
        url=f"{cf.API_PATH}/api/login",
        data={
            "login": login,
            "password": password
        }
    )

    if req.status_code != 200:
        logger.msg("ERROR", f"Server Report Authorization Error: {req.status_code}, {req.text}")

        if "error" in req.json().keys() and req.json().get("error") == "Wrong login or password":
            await msg.edit_text("Неверный логин или пароль")
            return
        await msg.edit_text("Ошибка")
        return

    token = req.json().get("token")

    user_tokens_db.insert_user(
        tgid=str(user_id),
        token=token
    )

    logger.info(f"Authorized {user_id=}, {token=}")

    kb = IKM(inline_keyboard=[[IKB(text="В меню отчётов ↩️", callback_data="report_main_menu")]])
    await msg.edit_text("Успешно ✅", reply_markup=kb)


# @router.message(Command('server_authorize'))
# async def authorize_command(msg: Message):
#     await msg.answer("Command: authorize")
#
#     loading_msg = await msg.answer("...")
#
#
#
#
#
#     user_tokens_db.insert_user(
#         tgid=str(msg.from_user.id),
#         token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiIxIiwic2x1ZyI6IlJPR0FMSUsiLCJpYXQiOjE3MzMzMjYzNjksImV4cCI6MTczMzQxMjc2OX0.5ttqvCo7itrS5t_6Cvzp6RRiA0AyaXuWbEHY2ZgQlT4"
#     )
#
#     await loading_msg.edit_text("Response: ok")






