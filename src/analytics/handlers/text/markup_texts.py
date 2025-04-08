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

    report = f"<b>Наценка:</b>\n\n"

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
        report += "\n".join(negative_changes) + "\n"

    # Вывод положительных изменений (если не указан only_negative)
    if not only_negative and positive_changes:
        report += "\n".join(positive_changes) + "\n"

    return report


def generate_markup_dish_report(data, period="month", only_negative=False):
    # Перевод периода на русский
    period_ru = PERIOD_TRANSLATION.get(period, "месяц")

    report = f"📊 <b>ТОП 5 позиций по наценке (за {period_ru}):</b>\n\n"

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
            negative_changes.append(f"{label}: {markup}%, изменение: {dynamics}%")
        else:
            positive_changes.append(f"{label}: {markup}%, изменение: {dynamics}%")

    # Вывод отрицательных изменений
    if negative_changes:
        report += "📉 <b>Снижение наценки:</b>\n"
        report += "\n".join(negative_changes) + "\n"

    # Вывод положительных изменений (если не указан only_negative)
    if not only_negative and positive_changes:
        report += "📈 <b>Рост наценки:</b>\n"
        report += "\n".join(positive_changes) + "\n"

    return report


# async def send_markup_report(message: Message, period="month", only_negative=False):
#     # Загрузка данных из файлов
#     with open("markup-store_example.json", "r", encoding="utf-8") as file:
#         store_data = json.load(file)

#     with open("markup-dish_example.json", "r", encoding="utf-8") as file:
#         dish_data = json.load(file)

#     # Генерация отчётов
#     store_report = generate_markup_store_report(store_data, period, only_negative)
#     dish_report = generate_markup_dish_report(dish_data, period, only_negative)

#     # Отправка отчётов в Telegram
#     await message.answer(store_report)
#     await message.answer(dish_report)


# # Команда /markup
# @dp.message(Command("markup"))
# async def handle_markup_command(message: Message):
#     args = message.text.split()
#     period = "month"  # По умолчанию отчёт за месяц
#     only_negative = False

#     # Обработка аргументов
#     if len(args) > 1:
#         if args[1] in ["week", "month", "year"]:
#             period = args[1]
#         elif args[1] == "negative":
#             only_negative = True

#     if len(args) > 2 and args[2] == "negative":
#         only_negative = True

#     await send_markup_report(message, period, only_negative)
