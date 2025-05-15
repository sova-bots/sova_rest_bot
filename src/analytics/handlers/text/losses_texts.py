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

    # Рост цен
    price_increase = sorted(
        [item for item in data["data"]
         if item.get(price_key_current) is not None and item.get(price_key_previous) is not None
         and item[price_key_current] > item[price_key_previous]],
        key=lambda x: x[loss_key],
        reverse=True
    )[:10]

    for item in price_increase:
        old_price = item[price_key_previous]
        new_price = item[price_key_current]
        loss = item[loss_key]
        report += f"• {item['label']} {old_price:,.0f} руб / {new_price:,.0f} руб / {loss:,.0f} руб\n"

    # Снижение цен
    if not only_negative:
        report += "\n<b>Снижение закупочных цен:</b>\n"
        report += "<b><i>цена старая / цена новая / факт экономии за период</i></b>\n\nТОП 10:\n"

        price_decrease = sorted(
            [item for item in data["data"]
             if item.get(price_key_current) is not None and item.get(price_key_previous) is not None
             and item[price_key_current] < item[price_key_previous]],
            key=lambda x: x[loss_key]
        )[:10]

        for item in price_decrease:
            old_price = item[price_key_previous]
            new_price = item[price_key_current]
            saving = abs(item[loss_key])  # экономию лучше брать по модулю
            report += f"• {item['label']} {old_price:,.0f} руб / {new_price:,.0f} руб / {saving:,.0f} руб\n"

    # Итоговая сумма
    total_loss = data["sum"][loss_key]
    if total_loss >= 0:
        summary_title = "<b>Общая сумма потерь за период:</b>"
    else:
        summary_title = "<b>Общая сумма экономии за период:</b>"

    report += f"\n{summary_title} {abs(total_loss):,.0f} руб"

    return [report.replace("-", "\\-").replace(".", "\\.")]

