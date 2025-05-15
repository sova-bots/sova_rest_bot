from ..types.text_data import TextData
from ..types.report_all_departments_types import ReportAllDepartmentTypes


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

    if "week" in period:
        dynamic_label = "динамика неделя"
    elif "month" in period:
        dynamic_label = "динамика месяц"
    elif "year" in period:
        dynamic_label = "динамика год"
    else:
        dynamic_label = ""

    kitchen_data = next((item for item in data["data"] if "Кухня" in item["label"]), None)
    bar_data = next((item for item in data["data"] if "Бар" in item["label"]), None)
    hozes_data = next((item for item in data["data"] if "Хозы" in item["label"]), None)

    report = f"<b>остатки на конец периода в днях / {dynamic_label}</b>\n\n"

    if kitchen_data:
        report += f"🥩 <b>Кухня:</b> {kitchen_data[turnover_key]:.0f} дней, {kitchen_data[dynamic_key]:+d}%\n"
    if bar_data:
        report += f"🍷 <b>Бар:</b> {bar_data[turnover_key]:.0f} дней, {bar_data[dynamic_key]:+d}%\n"
    if hozes_data:
        report += f"🧹 <b>Хозы:</b> {hozes_data[turnover_key]:.0f} дней, {hozes_data[dynamic_key]:+d}%\n"

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
        turnover = item.get(turnover_key)
        remainder_end = item.get("remainder_end")

        turnover_str = f"{turnover} дней" if turnover is not None else "<i>нет данных дней</i>"
        remainder_str = f"{remainder_end:,}".replace(",", " ") if remainder_end is not None else "<i>нет данных</i>"

        report_lines.append(f"• {item['label']}: {remainder_str} руб, {turnover_str}")

    main_report = turnover_text(text_data)[0]
    full_report = main_report.strip() + "\n\n" + "\n".join(report_lines)

    return [full_report]
