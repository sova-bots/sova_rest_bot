from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import logging

from src.analytics.auth.authorization import FSMReportAuthorization
from src.basic.keyboards.keyboards import to_start_kb
from ....data.notification.notification_google_sheets_worker import notification_gsworker

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router(name=__name__)


@router.callback_query(F.data == 'register')
async def registration_callback_handler(query: CallbackQuery, state: FSMContext) -> None:
    await registration_command_handler(query.message, state)
    await query.answer()


@router.message(Command('register'))
async def registration_command_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    logger.info(f"Начало регистрации для пользователя: {user_id}")

    answer = await message.answer('Загрузка ⚙️')

    # Проверяем, есть ли токен для этого пользователя
    token = notification_gsworker.get_token_by_user_id(user_id=user_id)

    if token is None:
        logger.info(f"Токен для пользователя {user_id} не найден")
        await answer.edit_text("Токен для вашего аккаунта не найден. Регистрация невозможна.")
        return

    # Если токен найден, регистрируем пользователя
    success = notification_gsworker.register_id(row=1, user_id=user_id)  # Укажите правильный row

    if success:
        logger.info(f"Пользователь {user_id} успешно зарегистрирован")
        await answer.edit_text('Вы успешно зарегистрированы в системе ✅', reply_markup=to_start_kb())
    else:
        logger.error(f"Пользователь {user_id} уже зарегистрирован")
        await answer.edit_text('Такой пользователь уже зарегистрирован в системе ❌', reply_markup=to_start_kb())


@router.callback_query(F.data == "auth")
async def auth_callback_handler(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()  # Ответим на callback, чтобы убрать "часики" на кнопке
    await query.message.answer("Авторизация больше не требуется. Используйте команду /register для регистрации.")


@router.message(Command('get_token'))
async def get_token_handler(message: Message) -> None:
    user_id = message.from_user.id
    logger.info(f"Запрос токена для пользователя: {user_id}")

    # Получаем токен по Telegram ID
    token = notification_gsworker.get_token_by_user_id(user_id=user_id)

    if token is None:
        logger.info(f"Токен для пользователя {user_id} не найден")
        await message.answer("Токен для вашего аккаунта не найден.")
        return

    # Если токен найден, отправляем его пользователю
    logger.info(f"Токен для пользователя {user_id}: {token}")
    await message.answer(f"Ваш токен: `{token}`", parse_mode="Markdown")