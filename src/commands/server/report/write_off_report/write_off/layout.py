from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from ...report_util import ReportRequestData, get_report_parameters_from_state, get_department_name, get_reports, get_reports_from_data, report_periods

router = Router(name=__name__)


@router.callback_query(F.data == "losses_write_off_menu")
async def losses_write_off_menu(query: CallbackQuery, state: FSMContext):
    await write_off_layout_msg(query, state)
    await query.answer()


async def write_off_layout_msg(query: CallbackQuery, state: FSMContext):
    assert isinstance(query.message, Message)

    period = (await state.get_data())['report_period']
    department_name = await get_department_name((await state.get_data())['report_department'], query.from_user.id)

    kb = IKM(inline_keyboard=[
                [IKB(text="Показатели 📊 ", callback_data="write_off_show_parameters")],
                [IKB(text="Обратите внимание 👀", callback_data="write_off_only_negative")],
                [IKB(text="Рекомендации 💡", callback_data="write_off_recomendations")]
            ])

    await state.set_state(None)
    await query.message.edit_text(f"Объект: <b>{department_name}</b>\nОтчёт: <b>Потери списания</b>\nПериод: <b>{report_periods[period]}</b>", reply_markup=kb)



@router.callback_query(F.data == "write_off_show_parameters")
async def losses_write_off_show_parameters_handler(query: CallbackQuery, state: FSMContext):
    assert isinstance(query.message, Message)

    period = (await state.get_data())['report_period']
    department_name = await get_department_name((await state.get_data())['report_department'], query.from_user.id)

    await query.message.edit_text("Загрузка... ⌛")

    request_data = ReportRequestData(
        user_id=query.from_user.id,
        state_data=(await state.get_data()),
    )

    data = await get_reports_from_data(query, request_data)

    header = f"Объект: <b>{department_name}</b>\nОтчёт: <b>Потери списания</b>\nПериод: <b>{report_periods[period]}"

    for report in data["data"]:
        text = f"""
<b>Витрина</b>:
<b>Служебное питание</b>:
<b>Бракераж</b>:
<b>Фритюр</b>:

<b>Хозы</b>:
"""

        await query.message.edit_text(f"{report=}")

    await query.answer()



@router.callback_query(F.data == "write_off_recomendations")
async def losses_write_off_recomendations_handler(query: CallbackQuery, state: FSMContext):
    assert isinstance(query.message, Message)

    text = """
<b>Рекомендации</b>:

1. Для минимизации потерь проводите списания на регулярной основе, ежедневно или еженедельно, в зависимости от вида списания.

2. Назначьте отвтественных, которые будут контролировать корректность списаний и стремиться их минимизировать.

3. Разработайте систему мотивации/KPI для сотрудников, направленную на минимизацию списаний.

4. Установите допустимые лимиты по разным видам списаний/складов.

5. Контролируйте заявки товара, следите, чтобы не было перетарки на складах.

6. Проводите регулярные собрания с сотрудниками, с помощью платформы SOVA-rest, совместно смотрите, обсуждайте показатели, вовремя выявляйте перекосы, негативную динамику, оперативно устраняйте нарушения.
"""
    await query.message.answer(text)
    await query.answer()
