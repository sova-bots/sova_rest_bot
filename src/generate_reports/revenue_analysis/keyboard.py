from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from src.mailing.data.notification.notification_google_sheets_worker import notification_gsworker


def to_start_kb() -> IKM:
    back_to_start_button = IKB(text='Вернуться на главную ↩', callback_data='start')

    markup = IKM(inline_keyboard=[
        [back_to_start_button]
    ])
    return markup


def get_report_format_keyboard():
    keyboard = IKM(row_width=2)
    keyboard.add(
        IKB("PDF", callback_data="generate_json_report_pdf"),
        IKB("Excel", callback_data="generate_json_report_excel")
    )
    return keyboard

