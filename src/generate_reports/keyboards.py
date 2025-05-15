from aiogram import types
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

report_end_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="main_menu")
    ]
])
