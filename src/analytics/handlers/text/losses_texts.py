def losses_text(data: list, period: str, only_negative: bool) -> list[str]:
    data = data[0]
    report = "<b>Рост закупочных цен:</b>\n"
    report += "<b><i>цена старая / цена новая / факт потерь за период</i></b>\n\nТОП 10:\n"

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

    for i in range(len(price_increase)):
        item = price_increase[i]
        report += f"{i+1}. {item['label']} {item[price_key_previous]:,.0f} руб / {item[price_key_current]:,.0f} руб / {item[loss_key]:,.0f} руб\n"

    if not only_negative:
        report += "\n<b>Снижение закупочных цен:</b>\n"
        report += "<b><i>цена старая / цена новая / факт потерь за период</i></b>\n\nТОП 10:\n"

        price_decrease = sorted(
            [item for item in data["data"] if
            item[price_key_current] and item[price_key_previous] and item[price_key_current] < item[price_key_previous]],
            key=lambda x: x[loss_key]
        )[:10]

        for i in range(len(price_decrease)):
            item = price_decrease[i]
            report += f"{i+1}. {item['label']} {item[price_key_previous]:,.0f} руб / {item[price_key_current]:,.0f} руб / {item[loss_key]:,.0f} руб\n"

    total_loss = data["sum"][loss_key]
        
    report += f"\n<b>Общая сумма потерь/прибыли за период:</b> {total_loss:,.0f} руб"

    return [report]