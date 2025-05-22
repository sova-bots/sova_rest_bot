from ..types.text_data import TextData


PERIOD_TRANSLATION = {
    "week": "неделю",
    "month": "месяц",
    "year": "год"
}


def make_markup_text(text_data: TextData):
    store_data = text_data.reports[0]

    if text_data.period in ["this-month", "last-month"]:
        period = "month"
    elif text_data.period in ["this-week", "last-week"]:
        period = "week"
    elif text_data.period in ["this-year", "last-year"]:
        period = "year"
    else:
        period = "month"

    only_negative = text_data.only_negative

    store_report = generate_markup_store_report(store_data, period, only_negative)

    return [store_report]


def make_markup_analysis_text(text_data: TextData):
    store_data = text_data.reports[0]
    dish_data = text_data.reports[1]

    if text_data.period in ["this-month", "last-month"]:
        period = "month"
    elif text_data.period in ["this-week", "last-week"]:
        period = "week"
    elif text_data.period in ["this-year", "last-year"]:
        period = "year"
    else:
        period = "month"

    only_negative = text_data.only_negative

    store_report = generate_markup_store_report(store_data, period, only_negative)
    dish_report = generate_markup_dish_report(dish_data, period, only_negative)

    return ["\n\n".join([store_report, dish_report])]


def generate_markup_store_report(data, period="month", only_negative=False):
    # Перевод периода на русский
    period_ru = PERIOD_TRANSLATION.get(period, "месяц")

    # Добавляем жирное форматирование для титульника
    report = f"<b>Наценка за {period_ru}:</b>\n\n"

    # Ключ для динамики
    dynamics_key = f"markup_dynamics_{period}"

    # Разделение на положительные и отрицательные изменения
    positive_changes = []
    negative_changes = []

    for item in data["data"]:
        label = item["label"]
        markup = item["markup"]
        dynamics = item.get(dynamics_key, 0)  # Получаем динамику по ключу

        if dynamics is None:
            continue

        if dynamics < 0:
            negative_changes.append(f"<b>{label}</b>:  {markup:,.1f}%")
        else:
            positive_changes.append(f"<b>{label}</b>:  {markup:,.1f}%")

    # Вывод отрицательных изменений
    if negative_changes:
        report += "<b>📉 Снижение наценки:</b>\n"  # Жирный заголовок для снижения
        report += "\n".join(negative_changes) + "\n"

    # Вывод положительных изменений (если не указан only_negative)
    if not only_negative and positive_changes:
        report += "<b>📈 Рост наценки:</b>\n"  # Жирный заголовок для роста
        report += "\n".join(positive_changes) + "\n"

    return report


def generate_markup_dish_report(data, period="month", only_negative=False):
    # Перевод периода на русский
    period_ru = PERIOD_TRANSLATION.get(period, "месяц")

    # Заголовок с динамикой для титульника
    report = f"<b>ТОП 5 позиций по наценке (за {period_ru}):</b>\n\n"

    # Ключ для динамики
    dynamics_key = f"markup_dynamics_{period}"

    # Сортировка данных по динамике наценки
    # Заменяем None на 0 для корректной сортировки
    sorted_data = sorted(data["data"], key=lambda x: x.get(dynamics_key, 0) or 0)

    # Разделение на положительные и отрицательные изменения
    positive_changes = []
    negative_changes = []

    for item in sorted_data[:5]:
        label = item["label"]
        markup = item["markup"]
        dynamics = item.get(dynamics_key, 0)  # Получаем динамику по ключу

        if dynamics is None:
            continue

        if dynamics < 0:
            negative_changes.append(f"{len(negative_changes) + 1}. {label}: {markup}%, изменение: {dynamics}%")
        else:
            positive_changes.append(f"{len(positive_changes) + 1}. {label}: {markup}%, изменение: {dynamics}%")

    # Вывод отрицательных изменений
    if negative_changes:
        report += "<b>📉 Снижение наценки:</b>\n"  # Жирный заголовок для снижения
        report += "\n".join(negative_changes) + "\n"

    # Вывод положительных изменений (если не указан only_negative)
    if not only_negative and positive_changes:
        report += "<b>📈 Рост наценки:</b>\n"  # Жирный заголовок для роста
        report += "\n".join(positive_changes) + "\n"

    return report
