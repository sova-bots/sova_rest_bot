from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from src.commands.server.util.db import user_tokens_db

router = Router(name=__name__)


@router.callback_query(F.data == "report_menu")
async def techsupport_cq_handler(query: CallbackQuery, state: FSMContext):
    assert isinstance(query.message, Message)

    user_id = query.from_user.id

    await state.clear()

    await query.message.answer(
        text="Меню ОТЧЁТЫ",
        reply_markup=get_markup(user_id)
    )

    await query.answer()


def get_markup(user_id) -> IKM:
    inline_kb = []

    if not user_tokens_db.has_tgid(user_id):
        btn = [IKB(text='Войти в систему', callback_data='server_report_authorization')]
        inline_kb.append(btn)
    else:
        btn = [IKB(text='Получить отчёт', callback_data='server_report_get')]
        inline_kb.append(btn)

    return IKM(inline_keyboard=inline_kb)
