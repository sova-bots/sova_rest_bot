from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from ...report_util import get_report_parameters_from_state, get_department_name, get_reports

router = Router(name=__name__)


@router.callback_query(F.data == "losses_write_off_menu")
async def losses_write_off_menu(query: CallbackQuery, state: FSMContext):
    await write_off_layout_msg(query, state)
    await query.answer()


async def write_off_layout_msg(query: CallbackQuery, state: FSMContext):
    period = (await state.get_data())['report_period']
    department_name = await get_department_name((await state.get_data())['report_department'], query.from_user.id)

    kb = IKM(inline_keyboard=[
                [IKB(text="Показатели 📊 ", callback_data="losses_write_off_show_parameters")],
                [IKB(text="Обратите внимание 👀", callback_data="losses_write_off_only_negative")],
                [IKB(text="Рекомендации 💡", callback_data="losses_write_off_recomendations")]
            ])
    
    await state.set_state(None)
    await query.message.answer(f"Объект: <b>{department_name}</b>\nОтчёт: <b>Потери списания</b>\nПериод: {period}", reply_markup=kb)


@router.callback_query(F.data == "losses_write_off_show_parameters")
async def losses_write_off_show_parameters_handler(query: CallbackQuery, state: FSMContext):
    period = (await state.get_data())['report_period']
    department_name = await get_department_name((await state.get_data())['report_department'], query.from_user.id)
    
    data = await get_reports(query, state)

    header = f"Объект: <b>{department_name}</b>\nОтчёт: <b>Потери списания</b>\nПериод: {period}"

    for report in data["data"]:
        text = f"""
<b>Витрина</b>: 
<b>Служебное питание</b>:
<b>Бракераж</b>:
<b>Фритюр</b>:

<b>Хозы</b>: 
"""

        await query.message.answer()

    await query.answer()



@router.callback_query(F.data == "losses_write_off_recomendations")
async def losses_write_off_recomendations_handler(query: CallbackQuery, state: FSMContext):
    text = """
<b>Рекомендации<b>:

1. Для минимизации потерь проводите списания на регулярной основе, ежедневно или еженедельно, в зависимости от вида списания.

2. Назначьте отвтественных, которые будут контролировать корректность списаний и стремиться их минимизировать.

3. Разработайте систему мотивации/KPI для сотрудников, направленную на минимизацию списаний.

4. Установите допустимые лимиты по разным видам списаний/складов.

5. Контролируйте заявки товара, следите, чтобы не было перетарки на складах.

6. Проводите регулярные собрания с сотрудниками, с помощью платформы SOVA-rest, совместно смотрите, обсуждайте показатели, вовремя выявляйте перекосы, негативную динамику, оперативно устраняйте нарушения.
"""
    await query.message.answer(text)

