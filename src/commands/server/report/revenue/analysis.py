from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

from ..report_util import get_reports_from_data, ReportRequestData

router = Router(name=__name__)


def f_dynamic(n: int) -> str:
    if n > 0:
        return f"+{n:,.0f}"
    return f"{n:,.0f}"


def make_one_text(r: dict, report_literal: str, label: str, period: str) -> tuple[str, bool]:
    period = period.split('-')[-1]
    
    dynamics = r[f'{report_literal}_dynamics_{period}']
    if dynamics > 0:
        dynamics = f"+{dynamics:,.0f}"
    else:
        dynamics = f"{dynamics:,.0f}"

    text = f"{label}: {dynamics}%; {r[f'{report_literal}_{period}']:,.0f} / {r[f'{report_literal}']:,.0f}"

    return text, r[f'{report_literal}_dynamics_{period}'] >= 0




@router.callback_query(F.data == "revenue_analysis")
async def revenue_analysis_handler(query: CallbackQuery, state: FSMContext):
    await query.message.edit_text("Загрузка... ⌛")

    data = ReportRequestData(
        user_id=query.from_user.id,
        state_data=(await state.get_data()),
    )
    data.report_type = "guests-checks"

    guests_checks_data = await get_reports_from_data(query, data)

    data.report_type = "avg-check"

    avg_check_data = await get_reports_from_data(query, data)

    data.report_type = "revenue"
    data.group = "store"

    revenue_stores_data = await get_reports_from_data(query, data)
    
    data.group = "department"
    
    revenue_data = await get_reports_from_data(query, data)
    
    period_literal = data.period.split('-')[-1]

    kb = IKM(inline_keyboard=[
        [IKB(text="Назад ↩️", callback_data="report")]
    ])

    msgs = (await state.get_data())['messages_to_delete'] if 'messages_to_delete' in (await state.get_data()).keys() and (await state.get_data())['messages_to_delete'] is not None else []

    for i in range(len(guests_checks_data["data"])):
        label = guests_checks_data["data"][i]["label"]

        avg_check_text, avg_check_positive = make_one_text(avg_check_data["data"][i], "avg_check", "\tсредний чек", data.period)
        checks_text, checks_positive = make_one_text(guests_checks_data["data"][i], "checks", "\tколичество чеков", data.period)

        text = f"<i>{label}</i>\n\n1. <b>Гостепоток и средний чек:</b>\n\n\"-\" "

        text += avg_check_text if not avg_check_positive else ""
        text += checks_text if not checks_positive else ""

        text += "\n\"+\" "

        text += avg_check_text if avg_check_positive else ""
        text += checks_text if checks_positive else ""

        text += f"\n\n2. <b>Выручка по направлениям:</b>\n\n "
        
        store_texts_positive = []
        store_texts_negative = []
        
        revenue_current = revenue_data["data"][i]["revenue"]
        revenue_last_period = revenue_data["data"][i][f"revenue_{period_literal}"]
        
        for store_data in revenue_stores_data["data"]:
            store_label = store_data['label']
            
            store_revenue_dynamic = store_data[f"revenue_dynamics_{period_literal}"]
            
            store_text = f"{store_label}: {f_dynamic(store_revenue_dynamic)}, {f_dynamic(store_data["revenue"] / revenue_last_period * 100)}% / {f_dynamic(store_data["revenue"] / revenue_current * 100)}%"

            print(f"{revenue_current=}, {revenue_last_period=}, {store_data=}")
            
            if store_revenue_dynamic > 0:
                store_texts_positive.append(store_text)
            else:
                store_texts_negative.append(store_text)
        
        text += "\"-\" "
        for store_text in store_texts_negative:
            text += store_text + "\n"
            
        text += "\"+\" "
        for store_text in store_texts_positive:
            text += store_text + "\n"
            
        msg = await query.message.answer(text, reply_markup=None)
        msgs.append(msg)

    await state.update_data({'messages_to_delete': msgs})

    await query.message.answer("Вернуться назад?", reply_markup=kb)

    await query.message.delete()   


    