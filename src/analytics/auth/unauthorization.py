import requests
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.types import Message

import config as cf
from src.analytics.db.db import user_tokens_db
from src.util.log import logger
from src.basic.keyboards.keyboards import to_start_kb

router = Router(name=__name__)


class FSMReportAuthorization(StatesGroup):
    ask_login = State()
    ask_password = State()


@router.callback_query(F.data == "analytics_report_unauthorize")
async def ask_to_proceed(query: CallbackQuery):

    kb = IKM(inline_keyboard=[
        [IKB(text="Да, уверен ✅", callback_data="analytics_report_unauthorize_proceed"), 
         IKB(text="Нет, назад ❌", callback_data="start")],
    ])
    await query.message.edit_text("Вы уверены, что хотите выйти из аккаунта?", reply_markup=kb)

    await query.answer()


@router.callback_query(F.data == "analytics_report_unauthorize_proceed")
async def unauthorize(query: CallbackQuery):

    tgid: int = query.from_user.id
    success = user_tokens_db.delete_user(tgid)

    if success:
        await query.message.edit_text("Успешно ✅", reply_markup=to_start_kb())

    await query.answer()



