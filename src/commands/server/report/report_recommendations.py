from datetime import datetime, timedelta

import requests
from aiogram import Router, F
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

import config as cf
from .report_util import *
from src.commands.server.util.db import user_tokens_db
from src.log import logger
from .text_problem_areas import get_problem_areas_text
from .text import get_report_text

router = Router(name=__name__)


recommendations = {
    "revenue": {
    "-5<dyn_week<0":
    """
Незначительное снижение выручки относительно прошлой недели. Рекомендуем понаблюдать за трендом и ориентироваться на динамику месяца и года - если они положительные, то повода для беспокойства пока нет.
    """,

    "dyn_week<-5":
    """
Такое снижение выручки в понедельной динамике может говорить о влиянии на выручку одного из факторов:
1. Праздничные дни и городвике мероприятия
2. Погодные условия
3. Маркетинговые акции и активности
4. Махинации сотрудников

Если этот тренд продолжается несколько недель, важно оценить динамику помесячно и по годам.
    """,

    "dyn_month<0":
    """
Снижение выручки в помесячной динамике может быть вызвано:

1. Сезонностью.
2. Количество календарных дней в месяце, а также соотношение будних, выходных и праздничных дней.
3. Для того, чтобы понять причину падения выручки, необходимо оценить:
- падение вызвано снижением гостепотока или среднего чека
- падение выручки по направлениям (бар, кухня и другие)
<b>- падение выручки по группам блюд
- падение выручки по отдельным часам посещения
- падение выручки по сотрудникам (средняя выручка, средний чек, наполняемость чека)</b>

Это позволит выявить, что именно стало причиной общего снижения оборота.
    """,

    "dyn_year<0":
    """
Если выручка снижается от года к году, на такое снижение следует обратить особо внимание. Перечислим основные причины:

Для того, чтобы понять причину падения выручки, необходимо оценить:
- падение вызвано снижением гостепотока или среднего чека
- падение выручки по направлениям (бар, кухня и другие)
<b>- падение выручки по группам блюд
- падение выручки по отдельным часам посещения
- падение выручки по сотрудникам (средняя выручка, средний чек, наполняемость чека)</b>
    """
    }
}


class RecommendationCallbackData(CallbackData, prefix="rprt-recs"):
    report_type: str
    recs_types: str


class ProblemAreasCallbackData(CallbackData, prefix="rprt-prars"):
    report_type: str


# Проблемные зоны
@router.callback_query(ProblemAreasCallbackData.filter(), FSMReportGeneral.idle)
async def problem_areas_callback_handler(query: CallbackQuery, callback_data: ProblemAreasCallbackData, state: FSMContext):
    cb_report_type = callback_data.report_type
    state_data = await state.get_data()
    report_parameters = get_report_parameters_from_state_data(state_data)

    # проверка
    if "report" not in state_data.keys() or state_data["report"] is None:
        await query.message.edit_text("Перезайдите в меню отчётов и получите отчёт ещё раз", reply_markup=IKM(inline_keyboard=[[IKB(text='В меню отчётов ↩️', callback_data='report_menu')]]))
        return

    report = state_data["report"]

    if report_parameters is None:
        await query.message.edit_text("Перезайдите в меню отчётов и получите отчёт ещё раз", reply_markup=IKM(inline_keyboard=[[IKB(text='В меню отчётов ↩️', callback_data='report_menu')]]))
        return

    report_type, report_departments, report_period = report_parameters

    if report_type != cb_report_type:
        await query.message.edit_text("Перезайдите в меню отчётов и получите отчёт ещё раз", reply_markup=IKM(inline_keyboard=[[IKB(text='В меню отчётов ↩️', callback_data='report_menu')]]))
        return
    
    # вывод характеристик
    text = ("<i>Проблемные характеристики: <b>{report_types.get(report_type)}</b></i> <i>за {report_periods.get(report_period)}:</i> 👇"
             + 
            get_problem_areas_text(report, report_type, report_departments, report_period))
    
    await query.message.answer(text, reply_markup=IKM(inline_keyboard=[[IKB(text='В меню отчётов ↩️', callback_data='report_menu')]]))
    await query.answer()


def get_revenue_recommendation_types(dynamic_week, dynamic_month, dynamic_year) -> str:
    types = []

    if dynamic_week is not None:
        if -5 < dynamic_week < 0:
            types.append("-5<dyn_week<0")
        elif dynamic_week < -5:
            types.append("dyn_week<-5")

    if dynamic_month is not None:
        if dynamic_month < 0:
            types.append("dyn_month<0")

    if dynamic_year is not None:
        if dynamic_year < 0:
            types.append("dyn_year<0")

    return ";".join(types)


@router.callback_query(RecommendationCallbackData.filter(F.report_type == "revenue"))
async def send_revenue_recs(query: CallbackQuery, callback_data: RecommendationCallbackData):
    texts = []

    for rec_type in callback_data.recs_types.split(';'):
        text = recommendations[callback_data.report_type][rec_type]
        texts.append(text)

    await query.message.answer("<b>Общий анализ 🔎</b>" + "\n".join(texts))

    await query.answer()
