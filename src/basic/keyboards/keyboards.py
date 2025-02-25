from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB


def to_start_kb() -> IKM:
    back_to_start_button = IKB(text='Вернуться на главную ↩', callback_data='start')

    markup = IKM(inline_keyboard=[
        [back_to_start_button]
    ])
    return markup
