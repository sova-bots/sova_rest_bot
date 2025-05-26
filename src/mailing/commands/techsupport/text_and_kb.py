from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from ...data.techsupport.techsupport_google_sheets_worker import TechSupportMessage


await_techsupport_question = """
Введите ваш вопрос.\nПостарайтесь максимально понятно и подробно описать вашу проблему, чтобы наши сотрудники могли в кратчайшие сроки вам помочь
"""


def get_ts_text(ts: TechSupportMessage) -> str:
    text = \
f"""
<b><i>Вопрос</i></b>
{ts.question}
"""
    return text


def get_answer_ts_kb(ts: TechSupportMessage) -> IKM:
    kb = IKM(inline_keyboard=[
        [IKB(text="Ответить", callback_data=f"ansTS:{ts.id}")]
    ])
    return kb


def get_answer_ts_client_text(ts: TechSupportMessage) -> str:
    return \
f"""
На ваше сообщение о тех-поддержке пришёл ответ!

<b><i>Вопрос:</i></b>
{ts.question}

<b><i>Ответ:</i></b>
{ts.answer}
"""
