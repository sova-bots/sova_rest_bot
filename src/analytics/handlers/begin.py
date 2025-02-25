from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

router = Router(name=__name__)


@router.callback_query(F.data == "analytics_begin")
async def analytics_begin_handler(query: CallbackQuery, state: FSMContext) -> None:
    await state.update_data({"report": None})

    

    await query.answer()


