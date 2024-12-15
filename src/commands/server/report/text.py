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
<b><i>{r['department']}</i></b>
    
<b>Выручка</b>: {f"{r['revenue']:,.0f} руб." if r['revenue'] is not None else "<i>нет данных</i>"}

{"Динамика выручки:" if r['dynamics_week'] is not None else ""}
{f"- Неделя: {dynamic_f(r['dynamics_week'])}" if r['dynamics_week'] is not None else ""}
{f"- Месяц: {dynamic_f(r['dynamics_month'])}" if r['dynamics_month'] is not None else ""}
{f"- Год: {dynamic_f(r['dynamics_year'])}" if r['dynamics_year'] is not None else ""}
""".strip("\n")


def report_guests_checks_text(r: dict) -> str:
    return f"""
<b><i>{r['department']}</i></b>
    
<b>Гости</b>: {f"{r['guests']:,.0f} чел." if r['guests'] is not None else "<i>нет данных</i>"}

{"Динамика гостей:" if r['guests_dynamics_week'] is not None else ""}
{f"- Неделя: {dynamic_f(r['guests_dynamics_week'])}" if r['guests_dynamics_week'] is not None else ""}
{f"- Месяц: {dynamic_f(r['guests_dynamics_month'])}" if r['guests_dynamics_month'] is not None else ""}
{f"- Год: {dynamic_f(r['guests_dynamics_year'])}" if r['guests_dynamics_year'] is not None else ""}
""".strip("\n")


def report_avg_check_text(r: dict) -> str:
    return f"""
<b><i>{r['department']}</i></b>
    
<b>Средний чек</b>: {f"{r['avg_check']:,.0f} руб." if r['avg_check'] is not None else "<i>нет данных</i>"}

{"Динамика среднего чека:" if r['avg_check_dynamics_week'] is not None else ""}
{f"- Неделя: {dynamic_f(r['avg_check_dynamics_week'])}" if r['avg_check_dynamics_week'] is not None else ""}
{f"- Месяц: {dynamic_f(r['avg_check_dynamics_month'])}" if r['avg_check_dynamics_month'] is not None else ""}
{f"- Год: {dynamic_f(r['avg_check_dynamics_year'])}" if r['avg_check_dynamics_year'] is not None else ""}
""".strip("\n")


def report_write_off_text(r: dict) -> str:
    return f"""
<b><i>{r['department']}</i></b>
    
<b>Списания</b>: {f"{r['write_off']:,.0f} руб." if r['write_off'] is not None else "<i>нет данных</i>"}

{"Динамика списаний:" if r['write_off_dynamics_week'] is not None else ""}
{f"- Неделя: {dynamic_f(r['write_off_dynamics_week'])}" if r['write_off_dynamics_week'] is not None else ""}
{f"- Месяц: {dynamic_f(r['write_off_dynamics_month'])}" if r['write_off_dynamics_month'] is not None else ""}
{f"- Год: {dynamic_f(r['write_off_dynamics_year'])}" if r['write_off_dynamics_year'] is not None else ""}
""".strip("\n")


def report_food_cost_general_text(r: dict) -> str:
    return f"""
{f"<b>Фудкост общий</b>: {f"{r['food_cost']:.0f}%" if r['food_cost'] is not None else "<i>нет данных</i>"}"}

{"Динамика общего фудкоста:" if r['food_cost_dynamics_week'] is not None else ""}
{f"- Неделя: {dynamic_f(r['food_cost_dynamics_week'])}" if r['food_cost_dynamics_week'] is not None else ""}
{f"- Месяц: {dynamic_f(r['food_cost_dynamics_month'])}" if r['food_cost_dynamics_month'] is not None else ""}
{f"- Год: {dynamic_f(r['food_cost_dynamics_year'])}" if r['food_cost_dynamics_year'] is not None else ""}
""".strip("\n")

def report_food_cost_kitchen_text(r: dict) -> str:
    return f"""
{f"<b>Фудкост кухня</b>: {f"{r['food_cost_kitchen']:.0f}%" if r['food_cost_kitchen'] is not None else "<i>нет данных</i>"}"}

{"Динамика фудкоста кухни:" if r['food_cost_kitchen_dynamics_week'] is not None else ""}
{f"- Неделя: {dynamic_f(r['food_cost_kitchen_dynamics_week'])}" if r['food_cost_kitchen_dynamics_week'] is not None else ""}
{f"- Месяц: {dynamic_f(r['food_cost_kitchen_dynamics_month'])}" if r['food_cost_kitchen_dynamics_month'] is not None else ""}
{f"- Год: {dynamic_f(r['food_cost_kitchen_dynamics_year'])}" if r['food_cost_kitchen_dynamics_year'] is not None else ""}
""".strip("\n")

def report_food_cost_bar_text(r: dict) -> str:
    return f"""
{f"<b>Фудкост бар</b>: {f"{r['food_cost_bar']:.0f}%" if r['food_cost_bar'] is not None else "<i>нет данных</i>"}"}

{"Динамика фудкоста бар:" if r['food_cost_bar_dynamics_week'] is not None else ""}
{f"- Неделя: {dynamic_f(r['food_cost_bar_dynamics_week'])}" if r['food_cost_bar_dynamics_week'] is not None else ""}
{f"- Месяц: {dynamic_f(r['food_cost_bar_dynamics_month'])}" if r['food_cost_bar_dynamics_month'] is not None else ""}
{f"- Год: {dynamic_f(r['food_cost_bar_dynamics_year'])}" if r['food_cost_bar_dynamics_year'] is not None else ""}
""".strip("\n")

def report_food_cost_text(r: dict) -> str:
    return f"""
<b><i>{r['department']}</i></b>

{report_food_cost_general_text(r).strip("\n")}

{report_food_cost_kitchen_text(r).strip("\n")}

{report_food_cost_bar_text(r).strip("\n")}
""".strip("\n")
