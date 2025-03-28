from ..types.text_data import TextData


def load_data_from_files(text_data: TextData):
    reports = text_data.reports
    
    # Загружаем данные из файлов
    guests_checks = reports[0]['sum']

    avg_check = reports[1]['sum']

    revenue_store = reports[3]['data']  # Используем данные из массива, а не сумму

    revenue_dish = reports[4]['data']  # Используем данные из массива, а не сумму

    revenue_time = reports[5]['data']

    revenue_date_of_week = reports[7]['data']

    revenue_waiter = reports[8]

    revenue_price_segments = reports[6]['data']

    # Формируем общий словарь с данными
    data = {
        'guests-checks': guests_checks,
        'avg-check': avg_check,
        'revenue-store': revenue_store,
        'revenue-dish': revenue_dish,
        'revenue-time': revenue_time,
        'revenue-date_of_week': revenue_date_of_week,
        'revenue-waiter': revenue_waiter,
        'revenue-price_segments': revenue_price_segments,
    }

    return data


def analyze_revenue(data, period="week"):
    # Определяем ключи для выбранного периода
    period_keys = {
        "week": {
            "revenue_key": "week",
            "dynamics_key": "dynamics_week",
            "label": "неделю"
        },
        "month": {
            "revenue_key": "month",
            "dynamics_key": "dynamics_month",
            "label": "месяц"
        },
        "year": {
            "revenue_key": "year",
            "dynamics_key": "dynamics_year",
            "label": "год"
        }
    }

    if period not in period_keys:
        raise ValueError("Неподдерживаемый период. Используйте 'week', 'month' или 'year'.")

    revenue_key = period_keys[period]["revenue_key"]
    dynamics_key = period_keys[period]["dynamics_key"]
    period_label = period_keys[period]["label"]

    # Заголовок отчёта с указанием периода
    message = (
        ""
    )

    # 1. Гостевой поток и средний чек
    guests_checks = data['guests-checks']
    avg_check = data['avg-check']
    message += (
        "<b> 1 Гостевой поток и средний чек:</b>\n\n"
    )

    # Собираем данные по динамике
    metrics = [
        {
            "label": "средний чек",
            "value": avg_check.get(f'avg_check_{dynamics_key}', 0),
            "current": avg_check.get('avg_check', 0),
            "previous": avg_check.get(f'avg_check_{revenue_key}', 0)
        },
        {
            "label": "глубина чека",
            "value": guests_checks.get(f'depth_{dynamics_key}', 0),
            "current": guests_checks.get('depth', 0),
            "previous": guests_checks.get(f'depth_{revenue_key}', 0)
        },
        {
            "label": "количество чеков",
            "value": guests_checks.get(f'checks_{dynamics_key}', 0),
            "current": guests_checks.get('checks', 0),
            "previous": guests_checks.get(f'checks_{revenue_key}', 0)
        }
    ]

    # Разделяем на отрицательные и положительные изменения
    negative_changes = [m for m in metrics if m['value'] < 0]
    positive_changes = [m for m in metrics if m['value'] >= 0]


    # Сначала выводим отрицательные изменения
    if negative_changes:
        message += "<i>Отрицательная динамика:</i>\n"
        for metric in negative_changes:
            message += (
                f"- {metric['label']}: {metric['value']:.1f}%, "
                f"{metric['previous']:,.0f} → {metric['current']:,.0f}\n"
            )
        message += "\n"

    # Затем выводим положительные изменения
    if positive_changes:
        message += "<i>Положительная динамика:</i>\n"
        for metric in positive_changes:
            message += (
                f"+ {metric['label']}: {metric['value']:.1f}%, "
                f"{metric['previous']:,.0f} → {metric['current']:,.0f}\n"
            )
        message += "\n"

    # 2. Выручка по направлениям (бар и кухня)
    revenue_store = data['revenue-store']

    # Суммируем выручку всех баров и всех кухонь за текущий и предыдущий периоды
    total_bar_revenue_current = sum(item['revenue'] for item in revenue_store if "Бар" in item['label'])
    total_bar_revenue_previous = sum(item[f'revenue_{revenue_key}'] for item in revenue_store if "Бар" in item['label'])

    total_kitchen_revenue_current = sum(item['revenue'] for item in revenue_store if "Кухня" in item['label'])
    total_kitchen_revenue_previous = sum(item[f'revenue_{revenue_key}'] for item in revenue_store if "Кухня" in item['label'])

    # Рассчитываем динамику изменения выручки (в процентах)
    bar_dynamics = ((
                            total_bar_revenue_current - total_bar_revenue_previous) / total_bar_revenue_previous) * 100 if total_bar_revenue_previous != 0 else 0
    kitchen_dynamics = ((
                                total_kitchen_revenue_current - total_kitchen_revenue_previous) / total_kitchen_revenue_previous) * 100 if total_kitchen_revenue_previous != 0 else 0

    # Формируем сообщение
    message += (
        "<b>2 Выручка по направлениям:</b>\n\n"
        f"{'+' if bar_dynamics == abs(bar_dynamics) else '-'} бар: {bar_dynamics:.1f}%, {total_bar_revenue_previous:,.0f} → {total_bar_revenue_current:,.0f}\n"
        f"{'+' if kitchen_dynamics == abs(kitchen_dynamics) else '-'} кухня: {kitchen_dynamics:.1f}%, {total_kitchen_revenue_previous:,.0f} → {total_kitchen_revenue_current:,.0f}\n\n"
    )

    # 3. Выручка по группам блюд
    revenue_dish = data['revenue-dish']
    if revenue_dish:
        message += "<b>3 Выручка по группам блюд:</b>\n\n"

        # Словарь для категорий блюд
        dish_categories = {
            "Салаты": [],
            "Супы": [],
            "Выпечка": [],
            "Кофе": [],
            "Другие": []  # Для всех остальных блюд
        }

        # Группируем блюда по категориям
        for dish in revenue_dish:
            label = dish['label'].lower()
            if "салат" in label:
                dish_categories["Салаты"].append(dish)
            elif "суп" in label:
                dish_categories["Супы"].append(dish)
            elif "выпечка" in label or "пирог" in label or "торт" in label:
                dish_categories["Выпечка"].append(dish)
            elif "кофе" in label or "капучино" in label or "латте" in label:
                dish_categories["Кофе"].append(dish)
            else:
                dish_categories["Другие"].append(dish)

        # Собираем данные по категориям
        category_data = []
        for category, dishes in dish_categories.items():
            if dishes:
                total_revenue_previous = sum(dish.get(f'revenue_{revenue_key}', 0) for dish in dishes)
                total_revenue_current = sum(dish.get('revenue', 0) for dish in dishes)
                total_dynamics = ((
                                              total_revenue_current - total_revenue_previous) / total_revenue_previous) * 100 if total_revenue_previous != 0 else 0

                category_data.append({
                    "category": category,
                    "dynamics": total_dynamics,
                    "revenue_previous": total_revenue_previous,
                    "revenue_current": total_revenue_current
                })


        # Сортируем категории по динамике (сначала отрицательные, затем положительные)
        negative_changes = [item for item in category_data if item['dynamics'] < 0]
        positive_changes = [item for item in category_data if item['dynamics'] >= 0]

        # Сначала выводим отрицательные изменения
        if negative_changes:
            message += "<i>Отрицательная динамика:</i>\n"
            for item in negative_changes:
                message += (
                    f"{item['category']}: {item['dynamics']:.1f}%, "
                    f"{item['revenue_previous']:,.0f} → {item['revenue_current']:,.0f}\n"
                )
            message += "\n"

        # Затем выводим положительные изменения
        if positive_changes:
            message += "<i>Положительная динамика:</i>\n"
            for item in positive_changes:
                message += (
                    f"{item['category']}: {item['dynamics']:.1f}%, "
                    f"{item['revenue_previous']:,.0f} → {item['revenue_current']:,.0f}\n"
                )
            message += "\n"

    # 4. Выручка по времени посещения
    revenue_time = data['revenue-time']
    message += "<b>4 Выручка по времени посещения:</b>\n\n"

    # Сортируем данные по динамике (сначала отрицательные, затем положительные)
    negative_changes = []
    positive_changes = []

    for time_slot in revenue_time:
        label = time_slot['label']
        dynamics = time_slot.get(f'revenue_{dynamics_key}', 0) or 0  # Используем 0, если динамика отсутствует
        revenue_previous = time_slot.get(f'revenue_{revenue_key}', 0)
        revenue_current = time_slot.get('revenue', 0)

        if dynamics < 0:
            negative_changes.append((label, dynamics, revenue_previous, revenue_current))
        else:
            positive_changes.append((label, dynamics, revenue_previous, revenue_current))

    # Сначала выводим отрицательные изменения
    if negative_changes:
        message += "<i>Отрицательная динамика:</i>\n"
        for label, dynamics, revenue_previous, revenue_current in negative_changes:
            message += f"{label}: {dynamics:.1f}%, {revenue_previous:,.0f} → {revenue_current:,.0f}\n"
        message += "\n"

    # Затем выводим положительные изменения
    if positive_changes:
        message += "<i>Положительная динамика:</i>\n"
        for label, dynamics, revenue_previous, revenue_current in positive_changes:
            message += f"{label}: {dynamics:.1f}%, {revenue_previous:,.0f} → {revenue_current:,.0f}\n"
        message += "\n"

    # 5. Выручка по ценовым сегментам
    revenue_price_segments = data.get('revenue-price_segments', [])
    message += "<b>5 Выручка по ценовым сегментам:</b>\n\n"

    if revenue_price_segments:
        negative_changes = []
        positive_changes = []

        for segment in revenue_price_segments:
            label = segment.get('label', '')
            dynamics = segment.get(f'revenue_{dynamics_key}', 0) or 0
            revenue_previous = segment.get(f'revenue_{revenue_key}', 0)
            revenue_current = segment.get('revenue', 0)

            if dynamics < 0:
                negative_changes.append((label, dynamics, revenue_previous, revenue_current))
            else:
                positive_changes.append((label, dynamics, revenue_previous, revenue_current))

        # Сначала выводим отрицательные изменения
        if negative_changes:
            message += "<i>Отрицательная динамика:</i>\n"
            for label, dynamics, revenue_previous, revenue_current in negative_changes:
                message += f"- {label}: {dynamics:.1f}%, {revenue_previous:,.0f} → {revenue_current:,.0f}\n"
            message += "\n"

        # Затем выводим положительные изменения
        if positive_changes:
            message += "<i>Положительная динамика:</i>\n"
            for label, dynamics, revenue_previous, revenue_current in positive_changes:
                message += f"+ {label}: {dynamics:.1f}%, {revenue_previous:,.0f} → {revenue_current:,.0f}\n"
            message += "\n"
    else:
        message += "Данные по ценовым сегментам отсутствуют.\n\n"


        # 6. Выручка по дням недели
        revenue_date_of_week = data['revenue-date_of_week']
        message += "<b>6 Выручка по дням недели:</b>\n\n"

        if isinstance(revenue_date_of_week, list):
            # Сортируем дни по динамике (сначала отрицательные, затем положительные)
            days_of_week = {
                "Понедельник": "Пн",
                "Вторник": "Вт",
                "Среда": "Ср",
                "Четверг": "Чт",
                "Пятница": "Пт",
                "Суббота": "Сб",
                "Воскресенье": "Вс"
            }

            # Собираем данные по дням
            day_data = {}
            for full_day, short_day in days_of_week.items():
                day_info = next((item for item in revenue_date_of_week if item['label'] == full_day), None)
                if day_info:
                    day_data[short_day] = {
                        "dynamics": day_info.get(f'revenue_{dynamics_key}', 0),
                        "revenue_previous": day_info.get(f'revenue_{revenue_key}', 0),
                        "revenue_current": day_info.get('revenue', 0)
                    }

            # Разделяем дни на отрицательные и положительные
            negative_days = {day: data for day, data in day_data.items() if data['dynamics'] < 0}
            positive_days = {day: data for day, data in day_data.items() if data['dynamics'] >= 0}

            # Формируем сообщение
            if negative_days:
                message += "<i>Отрицательная динамика:</i>\n"
                for day, data in negative_days.items():
                    message += f"- {day}: {data['dynamics']:.1f}%, {data['revenue_previous']:,.0f} → {data['revenue_current']:,.0f}\n"
                message += "\n"

            if positive_days:
                message += "<i>Положительная динамика:</i>\n"
                for day, data in positive_days.items():
                    message += f"+ {day}: {data['dynamics']:.1f}%, {data['revenue_previous']:,.0f} → {data['revenue_current']:,.0f}\n"
                message += "\n"
        else:
            message += "Данные по дням недели отсутствуют или имеют неверный формат.\n\n"

    # 7. Выручка по сотрудникам
    revenue_waiter = data['revenue-waiter']
    if revenue_waiter and 'data' in revenue_waiter:
        waiters = revenue_waiter['data']
        message += "<b>7 Выручка по сотрудникам:</b>\n\n"

        # Потеря выручки (топ-10 сотрудников с наибольшей потерей)
        message += "<i>7.1 Потеря выручки по сотрудникам (топ-10):</i>\n"
        # Сортируем сотрудников по убыванию потери выручки
        loss_waiters = sorted(
            [waiter for waiter in waiters if waiter.get('revenue', 0) < 0],
            key=lambda x: x['revenue']
        )[:10]  # Берём только топ-10

        for waiter in loss_waiters:
            message += (
                f"{waiter['label']} {waiter['revenue']} руб\n"
                f"| среднедневная выручка {waiter['avg_revenue']:,.0f} руб\n"
                f"| средний чек {waiter['avg_checks']:,.0f} руб\n"
                f"| глубина чека {waiter['depth']}\n\n"
            )

        if not loss_waiters:
            message += "\t<i>-</i>\n\n"

        # Похвала сотрудникам (топ-10 сотрудников с наибольшей выручкой)
        message += "<i>7.2 Похвалите сотрудников (топ-10):</i>\n"
        # Сортируем сотрудников по убыванию выручки
        praise_waiters = sorted(
            [waiter for waiter in waiters if waiter.get('revenue', 0) > 0],
            key=lambda x: x['revenue'],
            reverse=True
        )[:10]  # Берём только топ-10

        for waiter in praise_waiters:
            message += (
                f"<b><i>{waiter['label']}</i></b>\n"
                f"| среднедневная выручка {waiter['avg_revenue']:,.0f} руб\n"
                f"| средний чек {waiter['avg_checks']:,.0f} руб\n"
                f"| глубина чека {waiter['depth']}\n\n"
            )

        if not praise_waiters:
            message += "\t<i>-</i>\n\n"

    return message
    


def revenue_analysis_text(text_data: TextData, msg_type: str = "") -> list[str]:
    data = load_data_from_files(text_data)

    if text_data.period in ["this-month", "last-month"]:
        period = "month"
    elif text_data.period in ["this-week", "last-week"]:
        period = "week"
    elif text_data.period in ["this-year", "last-year"]:
        period = "year"
    else:
        period = "month"

    only_negative = text_data.only_negative

    # Анализируем данные
    text = analyze_revenue(data, period)

    max_length = 4096

    parts = [text[i:i + max_length] for i in range(0, len(text), max_length)]

    return parts




# recommendations = {
#     "guests": """
# <b>Рекомендации:</b>
# Что можно сделать для увеличения количества гостей:
# 1. Повышение уровня сервиса, чистоты, атмосферы.
# 2. Повышение качества блюд, обновление меню.
# 3. Увеличение количества возвращаемости старых гостей (система лояльности, акции, подарки, внутренние мероприятия и пр.).
# 4. Привлечение новых гостей (рекламные кампании и PR, коллаборации с партнерами, участие во внешних мероприятиях и др.).
# 5. Обновление интерьера, рестайлинг, обновление/изменение концепции.
#     """.strip("\n"),
#     "avg_check": """
# <b>Рекомендации:</b>
# Что можно сделать для увеличения среднего чека и глубины чека:
# 1. Работа с сотрудниками: обучение и экзамен - продажи и знание меню; запуск мотивационных программ направленных на увеличение среднего чека и глубины чека.
# 2. Если есть возможность, в рамках концепции и в рамках мониторинга цен конкурентов, поднятие цен в меню.
# 3. Разработка и введение в меню новых позиций, с более высокой ценой, или позиций, которые хорошо использовать в качестве допродажи к действующим блюдам, напиткам.
#     """.strip("\n"),
#     "stores": """
# <b>Рекомендации:</b>
# Что делать при снижении выручки по направлению (кухня, бар), по группам блюд:
# Проведите продуктовый анализ (АВС-анализ и др.), определите сильные и слабые места, составьте план по корректировке ассортимента и цен в меню.
# Повысьте контроль качества сырья и готовых блюд.
# Контроль скорости отдачи блюд.
# Контроль полноты ассортимента и отсутствия стоп-листа. 
#     """.strip("\n"),
#     "days_of_week": """
# <b>Рекомендации:</b>
# С помощью маркетинговых инструментов привлекайте клиентов в проседающие дни недели.
#     """.strip("\n")
# }



def revenue_str_if_exists(name, value, properties, is_dynamic: bool) -> str:
    if name not in properties.keys() or value is None:
        return ""
    
    if is_dynamic:
        if value > 0:
            sign = "+"
        else:
            sign = ""
        return f"<b>{properties[name][0]}:</b> {sign}{value:,.0f} % \n"
    
    return f"<b>{properties[name][0]}:</b> {value:,.0f} {properties[name][1]} \n"


def revenue_text(text_data: TextData) -> list[str]:
    reports = text_data.reports[0]["data"]

    revenue_properties = {
        "properties1": {
            "revenue": ["Выручка", "руб"]
        },
        "dynamics": {
            "revenue_dynamics_week": ["Динамика неделя"],
            "revenue_dynamics_month": ["Динамика месяц"],
            "revenue_dynamics_year": ["Динамика год"],
        },
        "properties2": {
            "revenue_forecast": ["Прогноз", "руб"]
        }
    }
    texts = []
    is_one = len(reports) == 1
    for report in reports:
        if is_one:
            text = ""
        else:
            text = f"<code>{report.get("label")}</code>\n\n"

        for prop_type, props in revenue_properties.items():
            for k, v in report.items():
                is_dynamic = prop_type == "dynamics"
                text += revenue_str_if_exists(k, v, props, is_dynamic)
            text += '\n'
        texts.append(text)
    return texts


def f_dynamic(n: int) -> str:
    if n > 0:
        return f"+{n:,.0f}"
    return f"{n:,.0f}"


# def make_one_text(r: dict, report_literal: str, label: str, period: str) -> tuple[str, bool]:
#     period = period.split('-')[-1]
    
#     dynamics = r[f'{report_literal}_dynamics_{period}']

#     if dynamics is None:
#         pass
#     elif dynamics > 0:
#         dynamics = f"+{dynamics:,.0f}"
#     else:
#         dynamics = f"{dynamics:,.0f}"

#     last_parameter = f"{r[f'{report_literal}_{period}']:,.0f}" if r[f'{report_literal}_{period}'] is not None else None
#     parameter = f"{r[f'{report_literal}']:,.0f}" if r[f'{report_literal}'] is not None else None
#     text = f"{label}: {dynamics}%; {last_parameter} / {parameter}"

#     if r[f'{report_literal}_dynamics_{period}'] is not None:
#         positive = r[f'{report_literal}_dynamics_{period}'] >= 0
#     else:
#         positive = True

#     return text, positive


# def str_positive_negative(texts_positive: list[str], texts_negative: list[str], only_negative: bool) -> str:
#     text = ""

#     if not only_negative:
#         text += "\"-\" "
        
#     for t in texts_negative:
#         if t != texts_negative[0] and not only_negative:
#             text += "\t\t\t\t"
#         text += t + "\n"
    
#     if only_negative:
#         return text
    
#     text += "\"+\" "
#     for t in texts_positive:
#         if t != texts_positive[0]:
#             text += "\t\t\t\t"
#         text += t + "\n"
        
#     return text


# def revenue_analysis_text(text_data: TextData, msg_type: str = ""):
    
#     if not msg_type and text_data.only_negative:
#         msg_type = "only_negative"

#     period = text_data.period

#     guests_checks_data = text_data.reports[0]
#     avg_check_data = text_data.reports[1]
#     revenue_data = text_data.reports[2]
#     revenue_stores_data = text_data.reports[3]
#     revenue_date_of_week_data = text_data.reports[4]

#     text_list = []

#     for i in range(min(len(guests_checks_data["data"]), len(avg_check_data["data"]))):
#         label = guests_checks_data["data"][i]["label"]
        
#         period_literal = period.split('-')[-1]
        
#         only_negative = msg_type == "only_negative" or msg_type == "revenue_recomendations"
        
#         text = f"<i>{label}</i>\n\n"
        
#         guests_text, guests_positive = make_one_text(guests_checks_data["data"][i], "guests", "гостепоток", period)
#         avg_check_text, avg_check_positive = make_one_text(avg_check_data["data"][i], "avg_check", "средний чек", period)
#         checks_text, checks_positive = make_one_text(guests_checks_data["data"][i], "checks", "количество чеков", period)

#         check_texts_positive = []
#         check_texts_negative = []
        
#         if guests_positive:
#             check_texts_positive.append(guests_text)
#         else:
#             check_texts_negative.append(guests_text)
        
#         if avg_check_positive:
#             check_texts_positive.append(avg_check_text)
#         else:
#             check_texts_negative.append(avg_check_text)
            
#         if checks_positive:
#             check_texts_positive.append(checks_text)
#         else:
#             check_texts_negative.append(checks_text)
        
#         if msg_type != "revenue_recomendations":
#             text += "1. <b>Гостепоток и средний чек:</b>\n"
#             text += str_positive_negative(check_texts_positive, check_texts_negative, only_negative)
        
#         if msg_type == "revenue_recomendations" and not guests_positive:
#             text += f"1. <b>Гостепоток:</b>\n"
#             text += guests_text + "\n"
#             text += "\n" + recommendations['guests']
        
#         if msg_type == "revenue_recomendations" and not avg_check_positive:
#             text += f"1. <b>Средний чек:</b>\n"
#             text += avg_check_text + "\n"
#             text += checks_text + "\n"
#             text += "\n" + recommendations['avg_check']

#         text += "\n\n2. <b>Выручка по направлениям:</b>\n"
        
#         store_texts_positive = []
#         store_texts_negative = []
        
#         revenue_current = revenue_data["data"][i]["revenue"]
#         revenue_last_period = revenue_data["data"][i][f"revenue_{period_literal}"]
        
#         for store_data in revenue_stores_data["data"]:
#             store_label = store_data['label']
            
#             store_revenue_dynamic = store_data[f"revenue_dynamics_{period_literal}"]
#             store_revenue_dynamic = store_revenue_dynamic if store_revenue_dynamic is not None else "<i>нет данных</i>"
            
#             store_text = f"{store_label}: {f_dynamic(store_revenue_dynamic)}, {f_dynamic(store_data["revenue"] / revenue_last_period * 100)}% / {f_dynamic(store_data["revenue"] / revenue_current * 100)}%"
            
#             if isinstance(store_revenue_dynamic, int) and store_revenue_dynamic >= 0:
#                 store_texts_positive.append(store_text)
#             else:
#                 store_texts_negative.append(store_text)
        
#         text += str_positive_negative(store_texts_positive, store_texts_negative, only_negative)
        
#         if msg_type == "revenue_recomendations" and len(store_texts_negative) > 0:
#             text += "\n" + recommendations['stores'] + "\n"
        
#         text += "\n\n6. <b>Выручка по дням недели:</b>\n"
            
#         date_of_week_texts_positive = []
#         date_of_week_texts_negative = []
        
#         for date_of_week_data in revenue_date_of_week_data['data']:
#             weekdays = {"Понедельник": "пн", "Вторник": "вт", "Среда": "ср", "Четверг": "чт", "Пятница": "пт", "Суббота": "сб", "Воскресенье": "вс"}
            
#             date_of_week_dynamics = date_of_week_data[f"revenue_dynamics_{period_literal}"]
#             date_of_week_dynamics = date_of_week_dynamics if date_of_week_dynamics is not None else "<i>нет данных</i>"
            
#             date_of_week_text = f"{weekdays[date_of_week_data['label']]}: {date_of_week_dynamics}%"
            
#             if isinstance(date_of_week_dynamics, int) and date_of_week_dynamics >= 0:
#                 date_of_week_texts_positive.append(date_of_week_text)
#             else:
#                 date_of_week_texts_negative.append(date_of_week_text)
        
#         text += str_positive_negative(date_of_week_texts_positive, date_of_week_texts_negative, only_negative)
        
#         if msg_type == "revenue_recomendations" and len(date_of_week_texts_negative) > 0:
#             text += "\n" + recommendations['days_of_week'] + "\n"
        
#         text_list.append(text)

#     return text_list
