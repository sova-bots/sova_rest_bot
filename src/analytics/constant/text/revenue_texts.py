recommendations = {
    "guests": """
<b>Рекомендации:</b>
Что можно сделать для увеличения количества гостей:
1. Повышение уровня сервиса, чистоты, атмосферы.
2. Повышение качества блюд, обновление меню.
3. Увеличение количества возвращаемости старых гостей (система лояльности, акции, подарки, внутренние мероприятия и пр.).
4. Привлечение новых гостей (рекламные кампании и PR, коллаборации с партнерами, участие во внешних мероприятиях и др.).
5. Обновление интерьера, рестайлинг, обновление/изменение концепции.
    """.strip("\n"),
    "avg_check": """
<b>Рекомендации:</b>
Что можно сделать для увеличения среднего чека и глубины чека:
1. Работа с сотрудниками: обучение и экзамен - продажи и знание меню; запуск мотивационных программ направленных на увеличение среднего чека и глубины чека.
2. Если есть возможность, в рамках концепции и в рамках мониторинга цен конкурентов, поднятие цен в меню.
3. Разработка и введение в меню новых позиций, с более высокой ценой, или позиций, которые хорошо использовать в качестве допродажи к действующим блюдам, напиткам.
    """.strip("\n"),
    "stores": """
<b>Рекомендации:</b>
Что делать при снижении выручки по направлению (кухня, бар), по группам блюд:
Проведите продуктовый анализ (АВС-анализ и др.), определите сильные и слабые места, составьте план по корректировке ассортимента и цен в меню.
Повысьте контроль качества сырья и готовых блюд.
Контроль скорости отдачи блюд.
Контроль полноты ассортимента и отсутствия стоп-листа. 
    """.strip("\n"),
    "days_of_week": """
<b>Рекомендации:</b>
С помощью маркетинговых инструментов привлекайте клиентов в проседающие дни недели.
    """.strip("\n")
}



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


def revenue_text(reports: list) -> list[str]:
    reports = reports[0]["data"]

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


def make_one_text(r: dict, report_literal: str, label: str, period: str) -> tuple[str, bool]:
    period = period.split('-')[-1]
    
    dynamics = r[f'{report_literal}_dynamics_{period}']
    if dynamics > 0:
        dynamics = f"+{dynamics:,.0f}"
    else:
        dynamics = f"{dynamics:,.0f}"

    text = f"{label}: {dynamics}%; {r[f'{report_literal}_{period}']:,.0f} / {r[f'{report_literal}']:,.0f}"

    return text, r[f'{report_literal}_dynamics_{period}'] >= 0


def str_positive_negative(texts_positive: list[str], texts_negative: list[str], only_negative: bool) -> str:
    text = ""

    if not only_negative:
        text += "\"-\" "
        
    for t in texts_negative:
        if t != texts_negative[0] and not only_negative:
            text += "\t\t\t\t"
        text += t + "\n"
    
    if only_negative:
        return text
    
    text += "\"+\" "
    for t in texts_positive:
        if t != texts_positive[0]:
            text += "\t\t\t\t"
        text += t + "\n"
        
    return text


async def revenue_analysis(reports: list, period: str, msg_type: str):
    guests_checks_data = reports[0]
    avg_check_data = reports[1]


    data.report_type = "revenue"
    data.group = "store"
    
    data.group = "department"
    
    data.group = "date_of_week"


    for i in range(len(guests_checks_data["data"])):
        label = guests_checks_data["data"][i]["label"]
        
        period_literal = period.split('-')[-1]
        
        only_negative = msg_type == "only_negative" or msg_type == "revenue_recomendations"
        
        text = f"<i>{label}</i>\n\n"
        
        guests_text, guests_positive = make_one_text(guests_checks_data["data"][i], "guests", "гостепоток", period)
        avg_check_text, avg_check_positive = make_one_text(avg_check_data["data"][i], "avg_check", "средний чек", period)
        checks_text, checks_positive = make_one_text(guests_checks_data["data"][i], "checks", "количество чеков", period)

        check_texts_positive = []
        check_texts_negative = []
        
        if guests_positive:
            check_texts_positive.append(guests_text)
        else:
            check_texts_negative.append(guests_text)
        
        if avg_check_positive:
            check_texts_positive.append(avg_check_text)
        else:
            check_texts_negative.append(avg_check_text)
            
        if checks_positive:
            check_texts_positive.append(checks_text)
        else:
            check_texts_negative.append(checks_text)
        
        if msg_type != "revenue_recomendations":
            text += "1. <b>Гостепоток и средний чек:</b>\n"
            text += str_positive_negative(check_texts_positive, check_texts_negative, only_negative)
        
        if msg_type == "revenue_recomendations" and not guests_positive:
            text += f"1. <b>Гостепоток:</b>\n"
            text += guests_text + "\n"
            text += "\n" + recommendations['guests']
        
        if msg_type == "revenue_recomendations" and not avg_check_positive:
            text += f"1. <b>Средний чек:</b>\n"
            text += avg_check_text + "\n"
            text += checks_text + "\n"
            text += "\n" + recommendations['avg_check']

        text += "\n\n2. <b>Выручка по направлениям:</b>\n"
        
        store_texts_positive = []
        store_texts_negative = []
        
        revenue_current = revenue_data["data"][i]["revenue"]
        revenue_last_period = revenue_data["data"][i][f"revenue_{period_literal}"]
        
        for store_data in revenue_stores_data["data"]:
            store_label = store_data['label']
            
            store_revenue_dynamic = store_data[f"revenue_dynamics_{period_literal}"]
            store_revenue_dynamic = store_revenue_dynamic if store_revenue_dynamic is not None else "<i>нет данных</i>"
            
            store_text = f"{store_label}: {f_dynamic(store_revenue_dynamic)}, {f_dynamic(store_data["revenue"] / revenue_last_period * 100)}% / {f_dynamic(store_data["revenue"] / revenue_current * 100)}%"
            
            if isinstance(store_revenue_dynamic, int) and store_revenue_dynamic >= 0:
                store_texts_positive.append(store_text)
            else:
                store_texts_negative.append(store_text)
        
        text += str_positive_negative(store_texts_positive, store_texts_negative, only_negative)
        
        if msg_type == "revenue_recomendations" and len(store_texts_negative) > 0:
            text += "\n" + recommendations['stores'] + "\n"
        
        text += "\n\n6. <b>Выручка по дням недели:</b>\n"
            
        date_of_week_texts_positive = []
        date_of_week_texts_negative = []
        
        for date_of_week_data in revenue_date_of_week_data['data']:
            weekdays = {"Понедельник": "пн", "Вторник": "вт", "Среда": "ср", "Четверг": "чт", "Пятница": "пт", "Суббота": "сб", "Воскресенье": "вс"}
            
            date_of_week_dynamics = date_of_week_data[f"revenue_dynamics_{period_literal}"]
            date_of_week_dynamics = date_of_week_dynamics if date_of_week_dynamics is not None else "<i>нет данных</i>"
            
            date_of_week_text = f"{weekdays[date_of_week_data['label']]}: {date_of_week_dynamics}%"
            
            if isinstance(date_of_week_dynamics, int) and date_of_week_dynamics >= 0:
                date_of_week_texts_positive.append(date_of_week_text)
            else:
                date_of_week_texts_negative.append(date_of_week_text)
        
        text += str_positive_negative(date_of_week_texts_positive, date_of_week_texts_negative, only_negative)
        
        if msg_type == "revenue_recomendations" and len(date_of_week_texts_negative) > 0:
            text += "\n" + recommendations['days_of_week'] + "\n"
        
        msg = await query.message.answer(text, reply_markup=None)
        msgs.append(msg)

    await state.update_data({'messages_to_delete': msgs})

    await query.message.answer("Вернуться назад?", reply_markup=kb)

    await query.message.delete()


def revenue_analysis_text(reports: list) -> list[str]:
    pass