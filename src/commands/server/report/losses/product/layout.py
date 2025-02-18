from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from ...common_choices import common_period_msg, common_report_type_msg, common_report_layout_msg, get_common_header_msg
from ....report.report_util import ReportRequestData, get_reports_from_data
from ..local import FSMLosses, local_periods, local_report_types

router = Router(name=__name__)


async def product_next(query: CallbackQuery, state: FSMContext):
    await state.update_data()

    await common_report_layout_msg(
        query=query,
        state=state,
        local_report_types=local_report_types,
        local_periods=local_periods,
        kb = [
                [IKB(text="Показатели 📊 ", callback_data="losses_product_show_parameters")],
                [IKB(text="Обратите внимание 👀", callback_data="losses_product_only_negative")],
                [IKB(text="Рекомендации 💡", callback_data="losses_product_recomendations")]
        ]
    )


@router.callback_query(F.data == "losses_product_show_parameters")
async def parameters_handler(query: CallbackQuery, state: FSMContext):

    await query.message.edit_text("Загрузка... ⌛")

    request_data = ReportRequestData(
        user_id=query.from_user.id,
        state_data=(await state.get_data()),
    )

    request_data.report_type = "losses"
    request_data.group = "product"

    data = await get_reports_from_data(query, request_data)
    data = data['data']

    for report in data:
        header = await get_common_header_msg(query, state, report['label'], local_periods, local_report_types)
        await query.message.answer(text=f"{header}\n\n{report}")

    await query.answer()

