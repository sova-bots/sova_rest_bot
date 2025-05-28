from ..types.text_data import TextData
from ..types.report_all_departments_types import ReportAllDepartmentTypes


def to_float(value):
    """Преобразует строку в число, заменяет null/None/пустую строку на 0."""
    if value in [None, "null", "", "None"]:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def turnover_text(text_data: TextData) -> list[str]:
    if text_data.department == ReportAllDepartmentTypes.SUM_DEPARTMENTS_TOTALLY:
        return ["Отчёт в разработке"]

    period = text_data.period
    data = text_data.reports[0]

    period_mapping = {
        "this-week": ("turnover_in_days_week", "turnover_in_days_dynamic_week"),
        "last-week": ("turnover_in_days_week", "turnover_in_days_dynamic_week"),
        "this-month": ("turnover_in_days_month", "turnover_in_days_dynamic_month"),
        "last-month": ("turnover_in_days_month", "turnover_in_days_dynamic_month"),
        "this-year": ("turnover_in_days_year", "turnover_in_days_dynamic_year"),
        "last-year": ("turnover_in_days_year", "turnover_in_days_dynamic_year"),
    }

    if period not in period_mapping:
        return ["Ошибка: Некорректный период."]

    turnover_key, dynamic_key = period_mapping[period]

    dynamic_label = ""
    if "week" in period:
        dynamic_label = "динамика неделя"
    elif "month" in period:
        dynamic_label = "динамика месяц"
    elif "year" in period:
        dynamic_label = "динамика год"

    kitchen_data = next((item for item in data["data"] if "Кухня" in item["label"]), None)
    bar_data = next((item for item in data["data"] if "Бар" in item["label"]), None)
    hozes_data = next((item for item in data["data"] if "Хозы" in item["label"]), None)

    report = f"Оборачиваемость остатков:\n\nостатки на конец периода в днях / {dynamic_label}\n\n"

    if kitchen_data:
        turnover = to_float(kitchen_data.get(turnover_key))
        dynamic = to_float(kitchen_data.get(dynamic_key))
        report += f"🥩 <b>Кухня:</b> {turnover:.0f} дней, {dynamic:+.0f}%\n"

    if bar_data:
        turnover = to_float(bar_data.get(turnover_key))
        dynamic = to_float(bar_data.get(dynamic_key))
        report += f"🍷 <b>Бар:</b> {turnover:.0f} дней, {dynamic:+.0f}%\n"

    if hozes_data:
        turnover = to_float(hozes_data.get(turnover_key))
        dynamic = to_float(hozes_data.get(dynamic_key))
        report += f"🧹 <b>Хозы:</b> {turnover:.0f} дней, {dynamic:+.0f}%\n"

    return [report]


def product_turnover_text(text_data: TextData) -> list[str]:
    if text_data.department == ReportAllDepartmentTypes.SUM_DEPARTMENTS_TOTALLY:
        return ["Отчёт в разработке"]

    data = text_data.reports[1]
    period = text_data.period

    period_mapping = {
        "this-week": "turnover_in_days_week",
        "last-week": "turnover_in_days_week",
        "this-month": "turnover_in_days_month",
        "last-month": "turnover_in_days_month",
        "this-year": "turnover_in_days_year",
        "last-year": "turnover_in_days_year",
    }

    if period not in period_mapping:
        return ["Ошибка: Некорректный период."]

    turnover_key = period_mapping[period]

    report_lines = []
    for item in data["data"]:
        turnover = to_float(item.get(turnover_key))
        remainder_end = to_float(item.get("remainder_end"))

        formatted_price = f"{int(remainder_end):,}".replace(",", " ")
        report_lines.append(f"{item['label']}: {formatted_price} руб, {turnover:.0f} дней")

    report = turnover_text(text_data)[0] + "\n" + "\n• ".join(report_lines)

    return [report]
