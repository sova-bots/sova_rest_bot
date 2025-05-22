from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from src.mailing.data.notification.notification_google_sheets_worker import notification_gsworker


def to_start_kb() -> IKM:
    back_to_start_button = IKB(text='Вернуться на главную ↩', callback_data='start')

    markup = IKM(inline_keyboard=[
        [back_to_start_button]
    ])
    return markup


def get_markup(user_id: int, has_token: bool) -> IKM:
    inline_kb = []
    if not has_token:
        btn = [IKB(text='Меню отчётов', callback_data='server_report_authorization')]
    else:
        btn = [IKB(text='Меню отчётов', callback_data='analytics_report_begin')]
    inline_kb.append(btn)

    btn = [IKB(text='Меню тех-поддержки 🛠', callback_data='techsupport_menu')]
    inline_kb.append(btn)

    if notification_gsworker.contains_id(user_id):
        btn = [IKB(text='Отписаться от рассылки уведомлений ❌', callback_data='unregister')]
    else:
        btn = [IKB(text='Подписаться на рассылку уведомлений 📩', callback_data='register')]
    inline_kb.append(btn)

    btn = [IKB(text='Сформировать отчёт 📊', callback_data='generate_report')]
    inline_kb.append(btn)

    btn = [IKB(text='Сгенерировать примерный отчёт 📑', callback_data='generate_sample_report')]
    inline_kb.append(btn)

    btn = [IKB(text='Сформировать отчёт по JSON 📊', callback_data='generate_json_report')]
    inline_kb.append(btn)

    btn = [IKB(text='Задать вопрос ❓', callback_data='send_question')]
    inline_kb.append(btn)

    return IKM(inline_keyboard=inline_kb)


def get_report_format_keyboard():
    keyboard = IKM(row_width=2)
    keyboard.add(
        IKB("PDF", callback_data="generate_json_report_pdf"),
        IKB("Excel", callback_data="generate_json_report_excel")
    )
    return keyboard

