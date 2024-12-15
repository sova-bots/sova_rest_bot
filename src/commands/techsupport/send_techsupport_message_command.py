from aiogram import Router, html, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, User, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, ContentType
from unicodedata import category

from src.commands.techsupport import text_and_kb
from src.data.techsupport.techsupport_google_sheets_worker import techsupport_gsworker, Const, BUTTONS_DATA
from src.commands.start.start_keyboards import get_start_registration_markup, get_start_unregistration_markup
router = Router(name=__name__)



class FSMSendTechSupportMessage(StatesGroup):
    await_quiestion_input = State()
    await_photo_input = State()
    await_category_input = State()


def get_skip_photo_kb() -> IKM:
    skip_photo_kb = IKM(inline_keyboard=[
        [IKB(text="Пропустить фото ▶️", callback_data="techsupport_skip_photo")]
    ])
    return skip_photo_kb


# функция когда нажимается кнопка "Отправить сообщение в тех-поддержку"
@router.callback_query(F.data == "send_techsupport_message")
async def send_techsupport_callback_handler(query: CallbackQuery, state: FSMContext) -> None:
    await choice(query.message)
    await query.answer()


# функция когда боту отправляется комманда "/send_techsupport_message"
@router.message(Command("send_techsupport_message"))
async def command_send_techsupport_handler(message: Message) -> None:
    await choice(message)

async def choice(message: Message):

    keyboard = IKM(inline_keyboard=[
        [IKB(text=data["text"], callback_data=str(key))]
        for key, data in BUTTONS_DATA.items()
    ])
    await message.answer(
        "Здравствуйте. С чем вы столкнулись, хотите заказать отчёт? Выберите из нижеследующих Вариантов:",
        reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data.isdigit() and int(c.data) in BUTTONS_DATA)
async def handle_option(callback: CallbackQuery):
    option_index = int(callback.data)
    response_text = BUTTONS_DATA[option_index]["response"]
    sub_options = BUTTONS_DATA[option_index]["sub_options"]

    keyboard = IKM(inline_keyboard=[
        [IKB(text=sub_text, callback_data=f"{option_index}:{sub_idx}")]
        for sub_idx, sub_text in sub_options.items()
    ])

    await callback.message.edit_text(response_text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(lambda c: ":" in c.data)
async def sub_option_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        parent_index, sub_index = map(int, callback.data.split(":"))  # Разделяем индексы
        sub_option_text = BUTTONS_DATA[parent_index]["sub_options"][sub_index]
        response_text = f'Вы выбрали: {sub_option_text}'

        await state.set_state(FSMSendTechSupportMessage.await_quiestion_input)
        await state.set_data({
            'category': [parent_index,sub_index]
        })
        await callback.message.edit_text(response_text)
        await callback.answer()
        await send_techsupport_handler(callback.message.from_user, callback.message, state)
    except (ValueError, KeyError, IndexError) as e:
        await callback.answer("Произошла ошибка при обработке подварианта.")
        print(f"Error processing sub-option: {e}")


# функция, отвечающая за отправку сообщения в тех-поддержку
async def send_techsupport_handler(user: User, message_for_answer: Message, state: FSMContext) -> None:


    await message_for_answer.answer(text_and_kb.await_techsupport_question)


@router.message(FSMSendTechSupportMessage.await_quiestion_input)
async def get_techsupport_question(message: Message, state: FSMContext) -> None:

    question_text = message.text
    await state.update_data({'techsupport_question': question_text})

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
    parent_index, sub_index = data['category']
    await write_techsupport(
        category = BUTTONS_DATA[parent_index]["text"] + " -> " + BUTTONS_DATA[parent_index]["sub_options"][sub_index],
        question=data['techsupport_question'],
        photo_id=message.photo[-1].file_id,
        client_id=message.from_user.id,
        message=message
    )

    await state.clear()


@router.callback_query(FSMSendTechSupportMessage.await_photo_input, F.data == "techsupport_skip_photo")
async def skip_photo(query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    parent_index, sub_index = data['category']
    await write_techsupport(
        category = BUTTONS_DATA[parent_index]["text"] + " -> " + BUTTONS_DATA[parent_index]["sub_options"][sub_index],
        question=data['techsupport_question'],
        photo_id=Const.NO_DATA,
        client_id=query.from_user.id,
        message=query.message
    )

    await query.answer()
    await state.clear()


async def write_techsupport(category: str, question: str, photo_id: str, client_id: int, message: Message) -> None:
    msg = await message.answer("Загрузка ⚙️")

    techsupport_gsworker.write_techsupport(category, question, photo_id, client_id)

    await msg.edit_text("Ваш вопрос отправлен в тех-поддержку ✅\nОжидайте, скоро вам ответят.")
