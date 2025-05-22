from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from ...data.techsupport.techsupport_google_sheets_worker import techsupport_gsworker

router = Router(name=__name__)


@router.callback_query(F.data == "techsupport_menu")
async def techsupport_cq_handler(query: CallbackQuery):
    msg = await query.message.answer("Загрузка... ⏳")

    user_id = query.from_user.id
    username = query.from_user.username

    await msg.edit_text(
        text="Меню ТЕХ-ПОДДЕРЖКА 🛠",
        reply_markup=get_markup(user_id, username)
    )

    await query.answer()


def is_techsupport_admin(user_id, username):
    admin_usernames = techsupport_gsworker.get_admin_usernames()

    if user_id in techsupport_gsworker.get_admin_user_ids():
        return True

    if username in admin_usernames:
        row = admin_usernames.index(username) + 2
        techsupport_gsworker.write_admin_user_id(user_id, row)
        return True

    return False


def get_markup(user_id, username) -> IKM:
    inline_kb = []

    if is_techsupport_admin(user_id, username):
        btn = [IKB(text='Посмореть сообщения в тех-поддержку 🛠', callback_data='show_techsupport_messages')]
        inline_kb.append(btn)

    btn = [IKB(text='Отправить сообщение в тех-поддержку 🛠', callback_data='send_techsupport_message')]
    inline_kb.append(btn)
    
    btn = [IKB(text="В главное меню ↩️", callback_data="start")]
    inline_kb.append(btn)

    return IKM(inline_keyboard=inline_kb)

