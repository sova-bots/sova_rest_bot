from datetime import datetime, timedelta

import requests
from aiogram import Router, F
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

import config as cf
from src.commands.server.util.db import user_tokens_db
from src.log import logger

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

    await query.message.answer("<b>Рекомендации</b>" + "\n".join(texts))

    await query.answer()

