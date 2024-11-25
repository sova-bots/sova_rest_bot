from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.filters.state import StatesGroup, State

from src.commands.register.registration_form import RegistrationForm
from src.common.keyboards import to_start_kb
from src.data.notification.notification_google_sheets_worker import notification_gsworker

router = Router(name=__name__)


class RegistrationStates(StatesGroup):
    subdomain_input = State()
    login_input = State()
    password_input = State()


@router.callback_query(F.data == 'register')
async def registration_callback_handler(query: CallbackQuery, state: FSMContext) -> None:
    await registration_command_handler(query.message, state)
    await query.answer()


@router.message(Command('register'))
async def registration_command_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(RegistrationStates.subdomain_input)
    msg_text = \
    '''
<b>Регистрация</b>

Введите ваш поддомен платформы SOVA-rest
'''
    await message.answer(msg_text)


@router.message(RegistrationStates.subdomain_input)
async def subdomain_input_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(subdomain=message.text)

    await state.set_state(RegistrationStates.login_input)
    msg_text = 'Введите ваш логин платформы SOVA-rest'
    await message.answer(msg_text)


@router.message(RegistrationStates.login_input)
async def subdomain_input_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(login=message.text)

    await state.set_state(RegistrationStates.password_input)
    msg_text = 'Введите ваш пароль платформы SOVA-rest'
    await message.answer(msg_text)


@router.message(RegistrationStates.password_input)
async def subdomain_input_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(password=message.text)

    data = await state.get_data()
    form = RegistrationForm(data)

    await state.clear()
    answer = await message.answer('Загрузка ⚙️')

    row = notification_gsworker.get_form_row(form)
    if row is None:
        await answer.edit_text('Данные неверны ❌', reply_markup=to_start_kb())
        return

    user_id = message.from_user.id
    success = notification_gsworker.register_id(row=row, user_id=user_id)

    if success:
        await answer.edit_text('Вы успешно вошли в систему ✅', reply_markup=to_start_kb())
    else:
        await answer.edit_text('Такой пользователь уже зарегистрирован в системе ❌', reply_markup=to_start_kb())





