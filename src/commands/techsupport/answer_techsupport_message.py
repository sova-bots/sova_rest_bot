from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from colorama import Fore

from src.commands.techsupport.text_and_kb import get_answer_ts_client_text
from src.data.techsupport.techsupport_google_sheets_worker import techsupport_gsworker, TechSupportMessage, Const

from src.log import logger

router = Router(name=__name__)


class FSMAnswerTS(StatesGroup):
    await_answer = State()


@router.callback_query(F.data.startswith("ansTS"))
async def answer_techsupport_messages_handler(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    ts_id = query.data.split(":")[-1]

    await state.set_state(FSMAnswerTS.await_answer)
    await state.set_data({'TSId': ts_id})

    await query.message.answer("Введите ответ")

    await query.answer()


@router.message(FSMAnswerTS.await_answer)
async def write_answer(message: Message, state: FSMContext, bot: Bot) -> None:
    answer = message.text

    msg = await message.answer("Загрузка ⚙️")

    data = await state.get_data()
    _id = data['TSId']

    success = techsupport_gsworker.write_answer(
        _id=_id,
        answer=answer
    )

    if not success:
        await msg.edit_text("Ошибка. Попробуйте ещё раз.")
        return

    ts = techsupport_gsworker.get_techsupport_by_id(_id)

    print(f"client_id: {ts.client_id}")

    if ts.client_id is None or ts.client_id == "":
        await msg.edit_text("Ответ записан.")
        return

    await bot.send_message(
        chat_id=ts.client_id,
        text=get_answer_ts_client_text(ts)
    )

    await msg.edit_text("Ответ записан.\nУведомление клиенту отправлено.")

