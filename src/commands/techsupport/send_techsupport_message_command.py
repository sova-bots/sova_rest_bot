from aiogram import Router, html, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, User, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, ContentType

from src.commands.techsupport import text_and_kb
from src.data.techsupport.techsupport_google_sheets_worker import techsupport_gsworker, Const
from src.commands.start.start_keyboards import get_start_registration_markup, get_start_unregistration_markup

router = Router(name=__name__)


class FSMSendTechSupportMessage(StatesGroup):
    await_quiestion_input = State()
    await_photo_input = State()


def get_skip_photo_kb() -> IKM:
    skip_photo_kb = IKM(inline_keyboard=[
        [IKB(text="Пропустить фото ▶️", callback_data="techsupport_skip_photo")]
    ])
    return skip_photo_kb


# функция когда нажимается кнопка "Отправить сообщение в тех-поддержку"
@router.callback_query(F.data == "send_techsupport_message")
async def send_techsupport_callback_handler(query: CallbackQuery, state: FSMContext) -> None:
    await send_techsupport_handler(query.from_user, query.message, state)
    await query.answer()


# функция когда боту отправляется комманда "/send_techsupport_message"
@router.message(Command("send_techsupport_message"))
async def command_send_techsupport_handler(message: Message, state: FSMContext) -> None:
    await send_techsupport_handler(message.from_user, message, state)


# функция, отвечающая за отправку сообщения в тех-поддержку
async def send_techsupport_handler(user: User, message_for_answer: Message, state: FSMContext) -> None:
    await state.clear()

    await state.set_state(FSMSendTechSupportMessage.await_quiestion_input)
    await message_for_answer.answer(text_and_kb.await_techsupport_question)


@router.message(FSMSendTechSupportMessage.await_quiestion_input)
async def get_techsupport_question(message: Message, state: FSMContext) -> None:
    question_text = message.text
    await state.set_data({'techsupport_question': question_text})

    await message.answer(
        text="Пришлите фото вашей проблемы 📸",
        reply_markup=get_skip_photo_kb()
    )

    await state.set_state(FSMSendTechSupportMessage.await_photo_input)


@router.message(FSMSendTechSupportMessage.await_photo_input)
async def get_techsupport_question(message: Message, state: FSMContext) -> None:

    if message.content_type != ContentType.PHOTO:
        await message.answer(
            text="Пришлите фото или пропустите",
            reply_markup=get_skip_photo_kb()
        )
        return

    data = await state.get_data()

    await write_techsupport(
        question=data['techsupport_question'],
        photo_id=message.photo[-1].file_id,
        client_id=message.from_user.id,
        message=message
    )

    await state.clear()


@router.callback_query(FSMSendTechSupportMessage.await_photo_input, F.data == "techsupport_skip_photo")
async def skip_photo(query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()

    await write_techsupport(
        question=data['techsupport_question'],
        photo_id=Const.NO_DATA,
        client_id=query.from_user.id,
        message=query.message
    )

    await query.answer()
    await state.clear()


async def write_techsupport(question: str, photo_id: str, client_id: int, message: Message) -> None:
    msg = await message.answer("Загрузка ⚙️")

    techsupport_gsworker.write_techsupport(question, photo_id, client_id)

    await msg.edit_text("Ваш вопрос отправлен в тех-поддержку ✅\nОжидайте, скоро вам ответят.")
