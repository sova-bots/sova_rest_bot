from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from src.mailing.data.notification.notification_google_sheets_worker import notification_gsworker

router = Router(name=__name__)


@router.callback_query(F.data == "mailing_menu")
async def mailing_menu_callback_handler(query: CallbackQuery):
    await mailing_menu(query.message, query.from_user.id)
    await query.answer()
    
    
@router.message(Command("mailing"))
async def mailing_menu_command_handler(message: Message):
    await mailing_menu(message, message.from_user.id)
    
    
async def mailing_menu(message: Message, user_id):
    msg = await message.answer("Загрузка... ⏳")
    
    kb = []
    
    if notification_gsworker.contains_id(user_id):
        btn = [IKB(text='Отписаться от рассылки уведомлений ❌', callback_data='unregister')]
    else:
        btn = [IKB(text='Подписаться на рассылку уведомлений 📩', callback_data='register')]
    kb.append(btn)
    
    btn = [IKB(text="В главное меню ↩️", callback_data="start")]
    kb.append(btn)
    
    text = "<b>Меню рассылки 📬</b>"
    
    await msg.edit_text(text=text, reply_markup=IKM(inline_keyboard=kb))
    
    

