from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.filters.state import StatesGroup, State

from ....data.notification.notification_google_sheets_worker import notification_gsworker
from src.basic.keyboards.keyboards import to_start_kb
from .unregistration_keyboards import get_unregister_choice_markup

router = Router(name=__name__)


class RegistrationStates(StatesGroup):
    login_input = State()  # Убрали subdomain_input
    password_input = State()


@router.callback_query(F.data == 'unregister')
async def unregistration_callback_handler(query: CallbackQuery) -> None:
    await unregistration_command_handler(query.message)
    await query.answer()


@router.message(Command('unregister'))
async def unregistration_command_handler(message: Message) -> None:
    msg_text = '''
<b>Выход из системы</b>
Вы уверены, что хотите отписаться от рассылки уведомлений?
'''
    await message.answer(msg_text, reply_markup=get_unregister_choice_markup())


@router.callback_query(F.data == 'unregister_yes')
async def unregistration_yes_callback_handler(query: CallbackQuery) -> None:
    answer = await query.message.answer('Загрузка ⚙️')

    user_id = query.from_user.id
    success = notification_gsworker.remove_id(user_id)

    if success:
        await answer.edit_text('Вы успешно вышли из системы ✅', reply_markup=to_start_kb())
    else:
        await answer.edit_text('Вы не были зарегистрированы ❌', reply_markup=to_start_kb())

    await query.answer()