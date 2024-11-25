from aiogram import Router, html, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from src.data.notification.notification_google_sheets_worker import notification_gsworker
from src.data.techsupport.techsupport_google_sheets_worker import techsupport_gsworker
from src.commands.start.start_keyboards import get_start_registration_markup, get_start_unregistration_markup

router = Router(name=__name__)


@router.callback_query(F.data == 'start')
async def start_callback_handler(query: CallbackQuery, state: FSMContext) -> None:
    await start_handler(query.from_user.id, query.message, state)
    await query.answer()


@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await start_handler(message.from_user.id, message, state)


async def start_handler(user_id: int, message: Message, state: FSMContext) -> None:
    await state.clear()

    msg = await message.answer("Загрузка ⚙️")

    admin_usernames = techsupport_gsworker.get_admin_usernames()
    username = message.from_user.username

    if user_id in techsupport_gsworker.get_admin_user_ids():
        is_admin = True
    elif username in admin_usernames:
        is_admin = True
        row = admin_usernames.index(username) + 2
        techsupport_gsworker.write_admin_user_id(user_id, row)
    else:
        is_admin = False

    await msg.edit_text(
        text=f"Вас приветствует чат-бот SOVA-tech!",
        reply_markup=get_markup(user_id, is_admin)
    )


def get_markup(user_id: int, is_admin: bool) -> IKM:
    inline_kb = []

    if is_admin:
        btn = [IKB(text='Посмореть сообщения в тех-поддержку 🛠', callback_data='show_techsupport_messages')]
        inline_kb.append(btn)

    btn = [IKB(text='Отправить сообщение в тех-поддержку 🛠', callback_data='send_techsupport_message')]
    inline_kb.append(btn)

    if notification_gsworker.contains_id(user_id):
        btn = [IKB(text='Отписаться от рассылки уведомлений ❌', callback_data='unregister')]
    else:
        btn = [IKB(text='Подписаться на рассылку уведомлений 📩', callback_data='register')]
    inline_kb.append(btn)

    return IKM(inline_keyboard=inline_kb)







