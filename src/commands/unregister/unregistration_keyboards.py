from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB


def get_unregister_choice_markup() -> IKM:
    unregister_yes_button = IKB(text='Да', callback_data='unregister_yes')
    unregister_no_button = IKB(text='Нет', callback_data='start')

    markup = IKM(inline_keyboard=[
        [unregister_yes_button, unregister_no_button]
    ])
    return markup
