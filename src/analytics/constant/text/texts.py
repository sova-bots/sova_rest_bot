from dataclasses import dataclass


@dataclass
class TextData:
    report: dict
    period: str
    only_negative: bool = False


# text functions
def text_func_example(text_data: TextData) -> str:
    report = text_data.report
    return f"{report=}"


def losses_text(data, period):
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
    "losses": lambda t: losses_text(t.report, t.period), 
    "loss-forecast": text_func_example
}





