from ..types.text_data import TextData


def forecast_text(text_data: TextData) -> list[str]:
    data = text_data.reports[0]
    period = text_data.period

    period_mapping = {
        "this-month": ("avg_price_two_week_ago", "avg_price_one_week_ago", "diff_price2"),
        "last-month": ("avg_price_three_week_ago", "avg_price_two_week_ago", "diff_price3"),
        "last-week": ("avg_price_four_week_ago", "avg_price_one_week_ago", "diff_price4"),
    }

    if period not in period_mapping:
        return ["Ошибка: Некорректный период."]

    old_price_key, new_price_key, loss_key = period_mapping[period]

    increasing_prices = []
    decreasing_prices = []

    for item in data["data"]:
        old_price = item.get(old_price_key)
        new_price = item.get(new_price_key)
        forecast_loss = round(item.get("forecast", 0), 2)

        if old_price is not None and new_price is not None:
            if new_price > old_price:
                increasing_prices.append((item["label"], old_price, new_price, forecast_loss))
            elif new_price < old_price:
                decreasing_prices.append((item["label"], old_price, new_price, forecast_loss))

    increasing_prices.sort(key=lambda x: x[3], reverse=True)
    decreasing_prices.sort(key=lambda x: x[3], reverse=True)

    total_loss = round(data["sum"].get("forecast", 0))

    result_text = """
🔥 <b>Рост закупочных цен:</b>
<b><i>цена старая / цена новая / прогноз потерь за период</i></b>
🔝 ТОП 10:
""" + "\n".join(
        [f"{i + 1}. {name} {old} руб / {new} руб / {loss:,.0f} руб"
         for i, (name, old, new, loss) in enumerate(increasing_prices[:10])])

    if not text_data.only_negative:
        result_text += """
<b>Снижение закупочных цен:</b>
<b><i>цена старая / цена новая / прогноз экономии за период</i></b>
🔝 ТОП 10:
""" + "\n".join(
            [f"{i + 1}. {name} {old} руб / {new} руб / -{abs(loss):,.0f} руб"
             for i, (name, old, new, loss) in enumerate(decreasing_prices[:10])])

    if total_loss > 0:
        total_summary = f"\n\n💰 <b>Общая сумма потерь за период:</b> {total_loss:,} руб"
    elif total_loss < 0:
        total_summary = f"\n\n💰 <b>Общая сумма экономии за период:</b> {abs(total_loss):,} руб"
    else:
        total_summary = f"\n\n💰 <b>Суммарных изменений не выявлено за период</b>"

    result_text += total_summary

    return [result_text.strip()]
