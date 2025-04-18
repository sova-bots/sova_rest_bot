from aiogram import types
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from src.analytics.constant.variants import all_periods

periodicity_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Ежедневно", callback_data="sub_daily")],
        [types.InlineKeyboardButton(text="По будням (Пн-Пт)", callback_data="sub_workdays")],
        [types.InlineKeyboardButton(text="Еженедельно", callback_data="sub_weekly")],
        [types.InlineKeyboardButton(text="Ежемесячно", callback_data="sub_monthly")]
    ])


timezone_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="МСК-1", callback_data="tz_-1"), InlineKeyboardButton(text="МСК", callback_data="tz_0")],
    [InlineKeyboardButton(text="МСК+1", callback_data="tz_1"),
     InlineKeyboardButton(text="МСК+2", callback_data="tz_2")],
    [InlineKeyboardButton(text="МСК+2", callback_data="tz_2"),
     InlineKeyboardButton(text="МСК+3", callback_data="tz_3")],
    [InlineKeyboardButton(text="МСК+4", callback_data="tz_4"),
     InlineKeyboardButton(text="МСК+5", callback_data="tz_5")],
    [InlineKeyboardButton(text="МСК+6", callback_data="tz_6"),
     InlineKeyboardButton(text="МСК+7", callback_data="tz_7")],
    [InlineKeyboardButton(text="МСК+8", callback_data="tz_8"),
     InlineKeyboardButton(text="МСК+9", callback_data="tz_9")],

])


weekdays_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Понедельник", callback_data="day_0")],
            [InlineKeyboardButton(text="Вторник", callback_data="day_1")],
            [InlineKeyboardButton(text="Среда", callback_data="day_2")],
            [InlineKeyboardButton(text="Четверг", callback_data="day_3")],
            [InlineKeyboardButton(text="Пятница", callback_data="day_4")],
            [InlineKeyboardButton(text="Суббота", callback_data="day_5")],
            [InlineKeyboardButton(text="Воскресенье", callback_data="day_6")]
        ])

def get_action_report_markup(report_type: str) -> types.InlineKeyboardMarkup:
    """Создаём клавиатуру для выбора действия (сформировать отчёт сейчас или подписаться на рассылку)"""
    inline_kb = [
        [types.InlineKeyboardButton(text="Сформировать текстовый отчёт сейчас", callback_data=f"generate_text_{report_type}")],
        [types.InlineKeyboardButton(text="Сформировать отчёт-файл сейчас", callback_data=f"generate_now_{report_type}")],
        [types.InlineKeyboardButton(text="Подписаться на рассылку", callback_data=f"subscribe_{report_type}")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=inline_kb)


def get_report_markup() -> types.InlineKeyboardMarkup:
    """Создаём клавиатуру для выбора типа отчёта"""
    inline_kb = [
        [types.InlineKeyboardButton(text='Анализ выручки', callback_data='report_revenue_analysis')],
        [types.InlineKeyboardButton(text='Товарооборот', callback_data='report_turnover')],
        [types.InlineKeyboardButton(text='Товарооборот (для различных объектов)',
                                    callback_data='report_turnover_by_objects')],
        [types.InlineKeyboardButton(text='Прогнозирование потерь для товаров', callback_data='report_loss_forecast')],
        [types.InlineKeyboardButton(text='Инвентаризация на складе', callback_data='report_inventory')],
        [types.InlineKeyboardButton(text='Себестоимость продуктов', callback_data='report_food_cost')],
        [types.InlineKeyboardButton(text='Себестоимость продуктов (с изменениями)',
                                    callback_data='report_food_cost_dynamics')]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=inline_kb)


def get_report_markup() -> types.InlineKeyboardMarkup:
    """Создаём клавиатуру для выбора типа отчёта"""
    inline_kb = [
        [types.InlineKeyboardButton(text='Анализ выручки', callback_data='report_revenue_analysis')],
        [types.InlineKeyboardButton(text='Товарооборот', callback_data='report_turnover')],
        [types.InlineKeyboardButton(text='Товарооборот (для различных объектов)',
                                    callback_data='report_turnover_by_objects')],
        [types.InlineKeyboardButton(text='Прогнозирование потерь для товаров', callback_data='report_loss_forecast')],
        [types.InlineKeyboardButton(text='Инвентаризация на складе', callback_data='report_inventory')],
        [types.InlineKeyboardButton(text='Себестоимость продуктов', callback_data='report_food_cost')],
        [types.InlineKeyboardButton(text='Себестоимость продуктов (с изменениями)',
                                    callback_data='report_food_cost_dynamics')],
        # Дополнительные кнопки
        [types.InlineKeyboardButton(text="Выручка (текстовый отчёт)", callback_data="text_report_revenue")],
        [types.InlineKeyboardButton(text="Потери (текстовый отчёт)", callback_data="text_report_losses")],
        [types.InlineKeyboardButton(text="Закупки (текстовый отчёт)", callback_data="text_report_purchases")],
        [types.InlineKeyboardButton(text="Фудкост (текстовый отчёт)", callback_data="text_report_food_cost")],
        [types.InlineKeyboardButton(text="Оборачиваемость остатков (текстовый отчёт)", callback_data="text_report_turnover")],
        [types.InlineKeyboardButton(text="Антивор (текстовый отчёт)", callback_data="text_report_antitheft")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=inline_kb)




def get_format_markup(report_type: str) -> types.InlineKeyboardMarkup:
    """Создаём клавиатуру для выбора формата отчёта (PDF или Excel) в зависимости от типа отчёта"""
    inline_kb = []

    if report_type == 'revenue_analysis':
        inline_kb = [
            [types.InlineKeyboardButton(text="PDF revenue_analysis", callback_data=f"revenue_analysis_pdf")],
            [types.InlineKeyboardButton(text="Excel revenue_analysis", callback_data=f"revenue_analysis_excel")]
        ]
    elif report_type == 'turnover':
        inline_kb = [
            [types.InlineKeyboardButton(text="PDF turnover", callback_data=f"format_pdf_turnover")],
            [types.InlineKeyboardButton(text="Excel turnover", callback_data=f"format_excel_turnover")]
        ]
    elif report_type == 'turnover_by_objects':
        inline_kb = [
            [types.InlineKeyboardButton(text="PDF turnover_by_objects", callback_data=f"format_pdf_turnover_by_objects")],
            [types.InlineKeyboardButton(text="Excel turnover_by_objects", callback_data=f"format_excel_turnover_by_objects")]
        ]
    elif report_type == 'loss_forecast':
        inline_kb = [
            [types.InlineKeyboardButton(text="PDF loss_forecast", callback_data=f"format_pdf_loss_forecast")],
            [types.InlineKeyboardButton(text="Excel loss_forecast", callback_data=f"format_excel_loss_forecast")]
        ]
    elif report_type == 'inventory':
        inline_kb = [
            [types.InlineKeyboardButton(text="PDF inventory", callback_data=f"inventory_pdf")],
            [types.InlineKeyboardButton(text="Excel inventory", callback_data=f"inventory_excel")]
        ]
    elif report_type == 'food_cost':
        inline_kb = [
            [types.InlineKeyboardButton(text="PDF food_cost", callback_data=f"format_pdf_food_cost")],
            [types.InlineKeyboardButton(text="Excel food_cost", callback_data=f"format_excel_food_cost")]
        ]
    elif report_type == 'food_cost_dynamics':
        inline_kb = [
            [types.InlineKeyboardButton(text="PDF food_cost_dynamics", callback_data=f"format_pdf_food_cost_dynamics")],
            [types.InlineKeyboardButton(text="Excel food_cost_dynamics", callback_data=f"format_excel_food_cost_dynamics")]
        ]
    else:
        # Если report_type не распознан, возвращаем пустую клавиатуру или клавиатуру по умолчанию
        inline_kb = [
            [types.InlineKeyboardButton(text="PDF пусто", callback_data=f"default_pdf")],
            [types.InlineKeyboardButton(text="Excel пусто", callback_data=f"default_excel")]
        ]

    return types.InlineKeyboardMarkup(inline_keyboard=inline_kb)


report_mailing_format_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="PDF", callback_data="format_pdf")],
    [InlineKeyboardButton(text="Excel", callback_data="format_excel")]
])


periods_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=key)]
        for key, name in all_periods.items()
    ]
)

type_translation = {
    "daily": "ежедневную",
    "weekly": "еженедельную",
    "monthly": "ежемесячную",
    "workdays": "по будням"
}
