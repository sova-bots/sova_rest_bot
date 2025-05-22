from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest


from colorama import Fore

from .text_and_kb import get_ts_text, get_answer_ts_kb
from ...data.techsupport.techsupport_google_sheets_worker import techsupport_gsworker, TechSupportMessage, Const

from src.util.log import logger

router = Router(name=__name__)


@router.callback_query(F.data == "show_techsupport_messages")
async def show_techsupport_messages_handler(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    tslist: list[TechSupportMessage] = techsupport_gsworker.get_techsupport_by_admin_id(admin_id=query.from_user.id)

    if not tslist:
        await query.message.answer("Пока что сообщений нет")
        await query.answer()
        return

    for ts in tslist:
        try:
            if ts.photo_id == Const.NO_DATA or ts.photo_id == "":
                await query.message.answer(
                    text=get_ts_text(ts),
                    reply_markup=get_answer_ts_kb(ts)
                )
            else:
                await query.message.answer_photo(
                    photo=ts.photo_id,
                    caption=get_ts_text(ts),
                    reply_markup=get_answer_ts_kb(ts)
                )
        except TelegramBadRequest as e:
            logger.msg("ERROR", e.message, Fore.RED)

    await query.answer()

