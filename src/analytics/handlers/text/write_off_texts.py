from ..types.text_data import TextData

shortage_limit = 2.0
surplus_limit = 3.0


def safe_get(data: dict, key: str, placeholder: str = "<i>нет данных</i>", comma: bool = False) -> str:
    value = data.get(key)
    if value is None:
        return placeholder

    if comma and isinstance(value, (int, float)):  # Улучшаем проверку на числовые значения
        return f"{value:,.2f}"  # Форматируем число с двумя знаками после запятой

    return str(value)



def inventory_text(text_data: TextData) -> list[str]:
    data = text_data.reports[0]["data"]

    texts = []
    # Заголовок для инвентаризации
    texts.append("<b>Инвентаризация: Недостача и излишки</b>\n")

    for index in range(0, len(data), 3):
        text_group = ""
        for report in data[index:index + 3]:
            text = f"<b>{report['label'].split('.')[-1]}</b>\n"

            add_shortage = (report["shortage_percent"] is not None) and (
                    not text_data.only_negative or report["shortage_percent"] > shortage_limit)
            add_surplus = (report["surplus_percent"] is not None) and (
                    not text_data.only_negative or report["surplus_percent"] > surplus_limit)

            # Вычисление и добавление данных о недостаче
            if add_shortage:
                shortage = safe_get(report, 'shortage', '0')  # Сумма недостачи
                shortage_percent = safe_get(report, 'shortage_percent', '0')  # Процент недостачи
                text += f"• Недостача: {shortage} руб; {shortage_percent}% от с/с\n"

            # Вычисление и добавление данных об избытке
            if add_surplus:
                surplus = safe_get(report, 'surplus', '0')  # Сумма излишка
                surplus_percent = safe_get(report, 'surplus_percent', '0')  # Процент излишка
                text += f"• Излишки: {surplus} руб; {surplus_percent}% от с/с\n"

            # Если были добавлены данные о недостаче или избытке, добавляем текст
            if add_surplus or add_shortage:
                text_group += text + "\n"

        if text_group:
            texts.append(text_group)

    if len(texts) == 0:
        return ["Все показатели в пределах нормы"]

    return texts



def write_off_text(text_data: TextData) -> list[str]:
    report = text_data.reports[0]["data"]

    period_mappings = {
        "this-week": "write_off_dynamics_week",
        "this-month": "write_off_dynamics_month",
        "this-year": "write_off_dynamics_year",
        "last-week": "write_off_dynamics_week",
        "last-month": "write_off_dynamics_month",
        "last-year": "write_off_dynamics_year",
    }

    dynamics_period_key = period_mappings.get(text_data.period, "write_off_dynamics_week")

    texts = [[]]
    count = 15
    cnt = 0
    cnt_texts = 0
    for item in report:
        write_off = f"{item['write_off']:,}" if item['write_off'] is not None else None
        write_off_dynamics = f"{item[dynamics_period_key]:.0f}" if item[dynamics_period_key] is not None else None

        if write_off is None or write_off_dynamics is None:
            continue

        if text_data.only_negative and item[dynamics_period_key] < 0:
            continue

        text = f"• <b>{item['label']}</b> {write_off} руб; {write_off_dynamics}%"
        texts[cnt_texts].append(text)
        cnt += 1

        if cnt >= count:
            texts.append([])
            cnt_texts += 1
            cnt = 0

    return ["\n\n".join(txt) for txt in texts]


# from ..types.text_data import TextData


# shortage_limit = 2.0
# surplus_limit = 3.0


# def safe_get(data: dict, key: str, placeholder: str = "<i>нет данных</i>", comma: bool = False) -> str:
#     value = data.get(key)
#     if value is None:
#         return placeholder

#     if comma and str(value).isdigit():
#         return f"{value:,}"

#     return value


# def inventory_text(text_data: TextData) -> list[str]:
#     data = text_data.reports[0]["data"]

#     texts = []
#     for index in range(0, len(data), 3):
#         text_group = ""
#         for report in data[index:index+3]:
#             text = f"<b>{report["label"].split('.')[-1]}</b>\n"
#             add_shortage = (report["shortage_percent"] is not None) and (not text_data.only_negative or report["shortage_percent"] > shortage_limit)
#             add_surplus = (report["surplus_percent"] is not None) and (not text_data.only_negative or report["surplus_percent"] > surplus_limit)
#             if add_shortage:
#                 text += f"• Недостача: {safe_get(report, "shortage", comma=True)} руб; {safe_get(report, "shortage_percent")}% от с/с\n"
#             if add_surplus:
#                 text += f"• Избыток: {safe_get(report, "surplus", comma=True)} руб; {safe_get(report, "surplus_percent")}% от с/с\n"
#             if add_surplus or add_shortage:
#                 text_group += text + "\n"
#         if text_group:
#             texts.append(text_group)

#     if len(texts) == 0:
#         return ["Все показатели в пределах нормы"]

#     return texts


# def write_off_text(text_data: TextData) -> list[str]:
#     report = text_data.reports[0]["data"]

#     period_mappings = {
#         "this-week": "write_off_dynamics_week",
#         "this-month": "write_off_dynamics_month",
#         "this-year": "write_off_dynamics_year",
#         "last-week": "write_off_dynamics_week",
#         "last-month": "write_off_dynamics_month",
#         "last-year": "write_off_dynamics_year",
#     }

#     dynamics_period_key = period_mappings[text_data.period]

#     texts = [[]]
#     count = 15
#     cnt = 0
#     cnt_texts = 0
#     for item in report:
#         write_off = f"{item["write_off"]:,}" if item["write_off"] is not None else None
#         write_off_dynamics = f"{item[dynamics_period_key]:.0f}" if item[dynamics_period_key] is not None else None

#         if write_off is None or write_off_dynamics is None:
#             continue

#         if text_data.only_negative and item[dynamics_period_key] < 0:
#             continue

#         text = f"• <b>{item["label"]}</b> {write_off} руб; {write_off_dynamics}%"
#         texts[cnt_texts].append(text)
#         cnt += 1

#         if cnt >= count:
#             texts.append([])
#             cnt_texts += 1
#             cnt = 0

#     return ["\n\n".join(txt) for txt in texts]
