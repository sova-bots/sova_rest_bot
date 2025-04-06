from ..types.text_data import TextData


period_mapping = {
        "this-week": "food_cost_dynamics_week",
        "last-week": "food_cost_dynamics_week",
        "this-month": "food_cost_dynamics_month",
        "last-month": "food_cost_dynamics_month",
        "this-year": "food_cost_dynamics_year",
        "last-year": "food_cost_dynamics_year",
    }


def foodcost_text(text_data: TextData) -> list[str]:
    cost_data = text_data.reports[0]
    period = text_data.period

    if period not in period_mapping:
        return "Ошибка: Некорректный период."

    period_key = period_mapping[period]

    # Текущие значения фудкоста
    kitchen_cost = cost_data["sum"].get("food_cost_kitchen", "Нет данных")
    bar_cost = cost_data["sum"].get("food_cost_bar", "Нет данных")

    kitchen_dynamic = cost_data["sum"].get(period_key, None)
    bar_dynamic = cost_data["sum"].get(period_key, None)

    # Форматирование динамики
    kitchen_dynamic_text = f", {kitchen_dynamic}%" if kitchen_dynamic not in [None, 0] else ""
    bar_dynamic_text = f", {bar_dynamic}%" if bar_dynamic not in [None, 0] else ""

    report = f"""<b>Кухня:</b> {kitchen_cost}%{kitchen_dynamic_text}\n<b>Бар:</b> {bar_cost}%{bar_dynamic_text}"""
    return [report]



def foodcost_analysis_text(text_data: TextData) -> list[str]:
    report = foodcost_text(text_data)[0]
    
    dish_data = text_data.reports[1]
    
    period_key = period_mapping[text_data.period]
    
    report += "\n"

    if not text_data.only_negative:
        report += "\n📉 ТОП 5 позиций по снижению фудкоста:\n"
        decreasing = [
            (item["label"], item["food_cost"], item["food_cost"] + item[period_key])
            for item in dish_data["data"] if item.get(period_key) is not None and item[period_key] <= 0
        ]
        decreasing.sort(key=lambda x: x[1] - x[2])
        cnt = 1
        for name, old, new in decreasing[:5]:
            report += f"{cnt}. {name}: {old}% → {new}%\n"
            cnt += 1

        if not decreasing:
            report += "Нет данных по снижению фудкоста.\n"

    report += "\n📈 ТОП 5 позиций по росту фудкоста:\n"
    increasing = [
        (item["label"], item["food_cost"], item["food_cost"] + item[period_key])
        for item in dish_data["data"] if item.get(period_key) is not None and item[period_key] > 0
    ]
    increasing.sort(key=lambda x: x[2] - x[1], reverse=True)
    cnt = 1
    for name, old, new in increasing[:5]:
        report += f"{cnt}. {name}: {old}% → {new}%\n"
        cnt += 1

    if not increasing:
        report += "Нет данных о росте фудкоста.\n"
        
    return [report]
