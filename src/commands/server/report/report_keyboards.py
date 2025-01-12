from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.filters.callback_data import CallbackData

from .report_util import reports_with_stores, problem_ares_show_negative, problem_ares_show_positive, get_department_index
from .report_stores import ReportStoreCallbackData
from .report_recommendations import ProblemAreasCallbackData, RecommendationCallbackData, get_revenue_recommendation_types


# Рекомендации (Общий анализ)
def get_recommendations_kb(report_type: str, report) -> list[list[IKB]]:
    ikb = []

    if report_type == "revenue":
            recommendation_types = get_revenue_recommendation_types(
                report['revenue_dynamics_week'],
                report['revenue_dynamics_month'],
                report['revenue_dynamics_year'],
            )
            if len(recommendation_types) > 0:
                ikb += [[IKB(text="Общий анализ 🔎", callback_data=RecommendationCallbackData(recs_types=recommendation_types, report_type=report_type).pack())]]

    return ikb


def get_problem_areas_kb(report_type: str) -> list[list[IKB]]:
    kb = [[IKB(text="Проблемные зоны 🎯", callback_data=ProblemAreasCallbackData(report_type))]]
    return kb


def get_report_kb(token, report_type, report, lenght_data):
    rkb = []

    # кнопка "Посмотреть по складам"
    if report_type in reports_with_stores:
        rkb += [[IKB(text='Посмотреть по складам', callback_data=ReportStoreCallbackData(department_index=str(get_department_index(report, token))).pack())]]

    # кнопки рекомендаций
    rkb += get_recommendations_kb(report_type, report)

    if report_type in problem_ares_show_positive or report_type in problem_ares_show_negative:
        rkb += get_problem_areas_kb(report_type)

    # кнопка "В меню отчётов"
    if lenght_data == 1:
        rkb += [[IKB(text='В меню отчётов ↩️', callback_data='report_menu')]]



