from src.log import logger
from .report_util import report_types, report_periods, problem_ares_show_negative, problem_ares_show_positive


def dynamic_f(dynamic) -> str:
    if dynamic > 0:
        sign = "+"
    elif dynamic < 0:
        sign = '-'
    else:
        sign = ""
    return f"{sign}{abs(dynamic):.0f}%"


def report_revenue_text(r: dict) -> str:
    return f"""
⏺️ <b><i>{r['label']}</i></b>
    
<b>Выручка</b>: {f"{r['revenue']:,.0f} руб." if r['revenue'] is not None else "<i>нет данных</i>"}

{"<b>Динамика выручки:</b>" if r['revenue_dynamics_week'] is not None else ""}
{f"• Неделя: {dynamic_f(r['revenue_dynamics_week'])}" if r['revenue_dynamics_week'] is not None else ""}
{f"• Месяц: {dynamic_f(r['revenue_dynamics_month'])}" if r['revenue_dynamics_month'] is not None else ""}
{f"• Год: {dynamic_f(r['revenue_dynamics_year'])}" if r['revenue_dynamics_year'] is not None else ""}
""".strip("\n")


def report_guests_checks_problem_areas_text(r: dict) -> str:
    return f"""
⏺️ <b><i>{r['label']}</i></b>
    
<b>Гости / чеки</b>: {f"{r['guests']:,.0f} / {r['checks']:,.0f}" if r['guests'] is not None and r['checks'] is not None else "<i>нет данных</i>"}

{"<b>Динамики:</b>" if r['guests_dynamics_week'] is not None else ""}
{f"• Неделя: {dynamic_f(r['guests_dynamics_week'])} / {dynamic_f(r['checks_dynamics_week'])}" if r['guests_dynamics_week'] is not None and r['checks_dynamics_week'] is not None and r['guests_dynamics_week'] < 0 else ""}
{f"• Месяц: {dynamic_f(r['guests_dynamics_month'])} / {dynamic_f(r['checks_dynamics_month'])}" if r['guests_dynamics_month'] is not None and r['checks_dynamics_month'] is not None and r['guests_dynamics_month'] < 0 else ""}
{f"• Год: {dynamic_f(r['guests_dynamics_year'])} / {dynamic_f(r['checks_dynamics_year'])}" if r['guests_dynamics_year'] is not None and r['checks_dynamics_year'] is not None and r['guests_dynamics_year'] < 0 else ""}
""".strip("\n")


def report_avg_check_text(r: dict) -> str:
    return f"""
⏺️ <b><i>{r['label']}</i></b>
    
<b>Средний чек</b>: {f"{r['avg_check']:,.0f} руб." if r['avg_check'] is not None else "<i>нет данных</i>"}

{"<b>Динамика среднего чека:</b>" if r['avg_check_dynamics_week'] is not None else ""}
{f"• Неделя: {dynamic_f(r['avg_check_dynamics_week'])}" if r['avg_check_dynamics_week'] is not None else ""}
{f"• Месяц: {dynamic_f(r['avg_check_dynamics_month'])}" if r['avg_check_dynamics_month'] is not None else ""}
{f"• Год: {dynamic_f(r['avg_check_dynamics_year'])}" if r['avg_check_dynamics_year'] is not None else ""}
""".strip("\n")


def report_write_off_text(r: dict) -> str:
    return f"""
⏺️ <b><i>{r['label']}</i></b>
    
<b>Списания</b>: {f"{r['write_off']:,.0f} руб." if r['write_off'] is not None else "<i>нет данных</i>"}

{"<b>Динамика списаний:</b>" if r['write_off_dynamics_week'] is not None else ""}
{f"• Неделя: {dynamic_f(r['write_off_dynamics_week'])}" if r['write_off_dynamics_week'] is not None else ""}
{f"• Месяц: {dynamic_f(r['write_off_dynamics_month'])}" if r['write_off_dynamics_month'] is not None else ""}
{f"• Год: {dynamic_f(r['write_off_dynamics_year'])}" if r['write_off_dynamics_year'] is not None else ""}
""".strip("\n")


def report_dangerous_operations_text(r: dict) -> str:
    return f"""
⏺️ <b><i>{r['label']}</i></b>
    
<b>Cумма опасных операция за пероид</b>: {f"{r['sum_dangerous_operations']:,.0f} руб." if r['sum_dangerous_operations'] is not None else "<i>нет данных</i>"}
<b>Опасные операции в % от выручки за пероид</b>: {f"{r['dangerous_operations_percent']:,.0f} руб." if r['dangerous_operations_percent'] is not None else "<i>нет данных</i>"}

{"<b>Динамика опасных операций:</b>" if r['dangerous_operations_dynamic_week'] is not None else ""}
{f"• Неделя: {dynamic_f(r['dangerous_operations_dynamic_week'])}" if r['dangerous_operations_dynamic_week'] is not None else ""}
{f"• Месяц: {dynamic_f(r['dangerous_operations_dynamic_month'])}" if r['dangerous_operations_dynamic_month'] is not None else ""}
{f"• Год: {dynamic_f(r['dangerous_operations_dynamic_year'])}" if r['dangerous_operations_dynamic_year'] is not None else ""}
""".strip("\n")


def report_food_cost_general_text(r: dict) -> str:
    return f"""
{f"<b>Фудкост общий</b>: {f"{r['food_cost']:.0f}%" if r['food_cost'] is not None else "<i>нет данных</i>"}"}

{"<b>Динамика общего фудкоста:</b>" if r['food_cost_dynamics_week'] is not None else ""}
{f"• Неделя: {dynamic_f(r['food_cost_dynamics_week'])}" if r['food_cost_dynamics_week'] is not None else ""}
{f"• Месяц: {dynamic_f(r['food_cost_dynamics_month'])}" if r['food_cost_dynamics_month'] is not None else ""}
{f"• Год: {dynamic_f(r['food_cost_dynamics_year'])}" if r['food_cost_dynamics_year'] is not None else ""}
""".strip("\n")

def report_food_cost_kitchen_text(r: dict) -> str:
    return f"""
{f"<b>Фудкост кухня</b>: {f"{r['food_cost_kitchen']:.0f}%" if r['food_cost_kitchen'] is not None else "<i>нет данных</i>"}"}

{"<b>Динамика фудкоста кухни:</b>" if r['food_cost_kitchen_dynamics_week'] is not None else ""}
{f"• Неделя: {dynamic_f(r['food_cost_kitchen_dynamics_week'])}" if r['food_cost_kitchen_dynamics_week'] is not None else ""}
{f"• Месяц: {dynamic_f(r['food_cost_kitchen_dynamics_month'])}" if r['food_cost_kitchen_dynamics_month'] is not None else ""}
{f"• Год: {dynamic_f(r['food_cost_kitchen_dynamics_year'])}" if r['food_cost_kitchen_dynamics_year'] is not None else ""}
""".strip("\n")

def report_food_cost_bar_text(r: dict) -> str:
    return f"""
{f"<b>Фудкост бар</b>: {f"{r['food_cost_bar']:.0f}%" if r['food_cost_bar'] is not None else "<i>нет данных</i>"}"}

{"<b>Динамика фудкоста бар:</b>" if r['food_cost_bar_dynamics_week'] is not None else ""}
{f"• Неделя: {dynamic_f(r['food_cost_bar_dynamics_week'])}" if r['food_cost_bar_dynamics_week'] is not None else ""}
{f"• Месяц: {dynamic_f(r['food_cost_bar_dynamics_month'])}" if r['food_cost_bar_dynamics_month'] is not None else ""}
{f"• Год: {dynamic_f(r['food_cost_bar_dynamics_year'])}" if r['food_cost_bar_dynamics_year'] is not None else ""}
""".strip("\n")

def report_food_cost_text(r: dict) -> str:
    return f"""
⏺️ <b><i>{r['label']}</i></b>

{report_food_cost_general_text(r).strip("\n")}

{report_food_cost_kitchen_text(r).strip("\n")}

{report_food_cost_bar_text(r).strip("\n")}
""".strip("\n")


def report_turnover_text(r: dict) -> str:
    return f"""
⏺️ <b><i>{r['label']}</i></b>

<b>Оборачиваемость в днях</b>: {f"{r['turnover_in_days']:,.0f}" if r['turnover_in_days'] is not None else "<i>нет данных</i>"}
<b>Расход в день</b>: {f"{r['expense_day']:,.0f} руб." if r['expense_day'] is not None else "<i>нет данных</i>"}

{"<b>Динамика оборачиваемости:</b>" if r['turnover_in_days_dynamic_week'] is not None else ""}
{f"• Неделя: {dynamic_f(r['turnover_in_days_dynamic_week'])}" if r['turnover_in_days_dynamic_week'] is not None else ""}
{f"• Месяц: {dynamic_f(r['turnover_in_days_dynamic_month'])}" if r['turnover_in_days_dynamic_month'] is not None else ""}
{f"• Год: {dynamic_f(r['turnover_in_days_dynamic_year'])}" if r['turnover_in_days_dynamic_year'] is not None else ""}
""".strip("\n")


def report_losses_text(r: dict) -> str:
    return f"""
⏺️ <b><i>{r['label']}</i></b>

<b>Потери текущий месяц к прошлому</b>: {f"{r['losses_current_month_to_last']:,.0f} руб." if r['losses_current_month_to_last'] is not None else "<i>нет данных</i>"}

<b>Потери прошлый месяц к позапрошлому</b>: {f"{r['losses_last_month_to_month_before_last']:,.0f} руб." if r['losses_last_month_to_month_before_last'] is not None else "<i>нет данных</i>"}

<b>Потери прошлая неделя к позапрошлой</b>: {f"{r['losses_last_week_to_week_before_last']:,.0f} руб." if r['losses_last_week_to_week_before_last'] is not None else "<i>нет данных</i>"}
""".strip("\n")



def get_problem_areas_text(report_type: str, report) -> str:
    match report_type:
        case "revenue":
            return report_revenue_text(report)
        case "guests-checks":
            return report_guests_checks_problem_areas_text(report)
        case "avg-check":
            return report_avg_check_text(report)
        case "write-off":
            return report_write_off_text(report)
        case "dangerous-operations":
            return report_dangerous_operations_text(report)
        case "food-cost":
            return report_food_cost_text(report)
        case "turnover":
            return report_turnover_text(report)
        case "losses":
            return report_losses_text(report)
        case _:
            logger.msg("ERROR", f"Error SendReports UnknownReportType: {report_type=}")
            raise Exception(f"Error SendReports UnknownReportType: {report_type=}")
    
