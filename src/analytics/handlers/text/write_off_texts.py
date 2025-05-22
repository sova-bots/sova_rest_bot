from ..types.text_data import TextData
from ..types.report_all_departments_types import ReportAllDepartmentTypes

shortage_limit = 2.0
surplus_limit = 3.0


def safe_get(data: dict, key: str, placeholder: str = "<i>нет данных</i>", comma: bool = False) -> str:
    value = data.get(key)
    if value is None:
        return placeholder

    if comma and str(value).isdigit():
        return f"{value:,}"

    return value


def inventory_text(text_data: TextData) -> list[str]:
    data = text_data.reports[0]["data"]

    # проверка, если нет данных
    if len(data) == 0:
        return ["Нет данных"]

    # прверка если итого
    if text_data.department == ReportAllDepartmentTypes.SUM_DEPARTMENTS_TOTALLY:
        data = [text_data.reports[0]["sum"]]
        data[0]["shortage_percent"] = round(data[0]["shortage"] / data[0]["cost_price"] * 1000) / 10
        data[0]["surplus_percent"] = round(data[0]["surplus"] / data[0]["cost_price"] * 1000) / 10

    texts = []
    for index in range(0, len(data), 3):
        text_group = ""
        for report in data[index:index + 3]:
            text = f"<b>{report['label'].split('.')[-1]}</b>\n"

            add_shortage = (
                report["shortage_percent"] is not None and
                (not text_data.only_negative or report["shortage_percent"] > shortage_limit)
            )
            add_surplus = (
                report["surplus_percent"] is not None and
                (not text_data.only_negative or report["surplus_percent"] > surplus_limit)
            )

            # Недостача
            if add_shortage:
                shortage = safe_get(report, 'shortage', '0')
                shortage_percent = safe_get(report, 'shortage_percent', '0')
                text += f"• Недостача: {shortage} руб; {shortage_percent}% от с/с\n"

            # Излишки
            if add_surplus:
                surplus = safe_get(report, 'surplus', '0')
                surplus_percent = safe_get(report, 'surplus_percent', '0')
                text += f"• Излишки: {surplus} руб; {surplus_percent}% от с/с\n"

            if add_shortage or add_surplus:
                text_group += text + "\n"

        if text_group:
            texts.append(text_group)

    if not texts:
        return ["Все показатели в пределах нормы"]

    # Добавляем заголовок перед первым блоком
    header = "📦 <b>Остатки / динамика</b>\n"
    texts[0] = header + texts[0]

    return texts



def write_off_text(text_data: TextData) -> list[str]:
    report = text_data.reports[0]["data"]

    # Отображаемое название периода
    period_labels = {
        "this-week": "неделя",
        "this-month": "месяц",
        "this-year": "год",
        "last-week": "неделя",
        "last-month": "месяц",
        "last-year": "год",
    }

    # Ключи динамики по периоду
    period_keys = {
        "this-week": "write_off_dynamics_week",
        "this-month": "write_off_dynamics_month",
        "this-year": "write_off_dynamics_year",
        "last-week": "write_off_dynamics_week",
        "last-month": "write_off_dynamics_month",
        "last-year": "write_off_dynamics_year",
    }

    # Определяем ключ и текст периода
    dynamics_key = period_keys[text_data.period]
    period_label = period_labels[text_data.period]

    texts = [[]]
    count = 15
    cnt = 0
    cnt_texts = 0

    for item in report:
        write_off_value = item.get("write_off")
        dynamics_value = item.get(dynamics_key)

        if write_off_value is None or dynamics_value is None:
            continue

        if text_data.only_negative and dynamics_value < 0:
            continue

        write_off_str = f"{int(write_off_value):,}".replace(",", " ")
        dynamics_str = f"{dynamics_value:.0f}%"

        text = f"• <b>{item['label']}</b> {write_off_str} руб; {dynamics_str}"
        texts[cnt_texts].append(text)
        cnt += 1

        if cnt >= count:
            texts.append([])
            cnt_texts += 1
            cnt = 0

    if not any(texts):
        return ["Нет данных по списаниям"]

    # Заголовок со ссылкой на период
    header = f"📉 <b>Списания / динамика {period_label}</b>\n"

    return [header + "\n".join(block) for block in texts if block]
