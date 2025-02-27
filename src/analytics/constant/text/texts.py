from dataclasses import dataclass


@dataclass
class TextData:
    reports: list
    period: str
    only_negative: bool = False


# text functions
def text_func_example(text_data: TextData) -> str:
    report = text_data.reports
    return f"{report=}"


# revenue
def revenue_str_if_exists(name, value, properties, is_dynamic: bool) -> str:
    if name not in properties.keys() or value is None:
        return ""
    
    if is_dynamic:
        if value > 0:
            sign = "+"
        else:
            sign = ""
        return f"<b>{properties[name][0]}:</b> {sign}{value:,.0f} % \n"
    
    return f"<b>{properties[name][0]}:</b> {value:,.0f} {properties[name][1]} \n"


def revenue_text(reports: list) -> str:
    report = reports[0]

    revenue_properties = {
        "properties1": {
            "revenue": ["Выручка", "руб"]
        },
        "dynamics": {
            "revenue_dynamics_week": ["Динамика неделя"],
            "revenue_dynamics_month": ["Динамика месяц"],
            "revenue_dynamics_year": ["Динамика год"],
        },
        "properties2": {
            "revenue_forecast": ["Прогноз", "руб"]
        }
    }

    text = ""
    print(f"{report=}")
    
    for prop_type, props in revenue_properties.items():
        for k, v in report.items():
            is_dynamic = prop_type == "dynamics"
            text += revenue_str_if_exists(k, v, props, is_dynamic)
        text += '\n'

    return text


# losses
def losses_text(data, period):
    data = data[0]
    report = "**Рост закупочных цен:**\n"
    report += "**цена старая / цена новая / факт потерь за период**\n\nТОП 10:\n"

    period_mapping = {
        "this-month": ("avg_price_current_month", "avg_price_last_month", "losses_current_month_to_last"),
        "last-month": ("avg_price_last_month", "avg_price_month_before_last", "losses_last_month_to_month_before_last"),
        "last-week": ("avg_price_last_week", "avg_price_week_before_last", "losses_last_week_to_week_before_last")
    }

    price_key_current, price_key_previous, loss_key = period_mapping.get(period, period_mapping["last-week"])

    price_increase = sorted(
        [item for item in data["data"] if
         item[price_key_current] and item[price_key_previous] and item[price_key_current] > item[price_key_previous]],
        key=lambda x: x[loss_key],
        reverse=True
    )[:10]

    for item in price_increase:
        report += f"{item['label']} {item[price_key_previous]} руб / {item[price_key_current]} руб / {item[loss_key]} руб\n"

    report += "\n**Снижение закупочных цен:**\n"
    report += "**цена старая / цена новая / факт потерь за период**\n\nТОП 10:\n"

    price_decrease = sorted(
        [item for item in data["data"] if
         item[price_key_current] and item[price_key_previous] and item[price_key_current] < item[price_key_previous]],
        key=lambda x: x[loss_key]
    )[:10]

    for item in price_decrease:
        report += f"{item['label']} {item[price_key_previous]} руб / {item[price_key_current]} руб / {item[loss_key]} руб\n"

    total_loss = data["sum"][loss_key]
    report += f"\n**Общая сумма потерь/прибыли за период:** {total_loss} руб"

    return report.replace("-", "\\-").replace(".", "\\.")


# key - report:type, value - make_text_func
text_functions = {
    "revenue": lambda text_data: revenue_text(text_data.reports),
    "losses": lambda text_data: losses_text(text_data.reports, text_data.period), 
    "loss-forecast": text_func_example,
}





