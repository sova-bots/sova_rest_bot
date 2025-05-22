import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.generate_reports.revenue_analysis.graphics_for_pdf import analys_revenue_pdf_router
from src.generate_reports.revenue_analysis.make_excel import analys_revenue_excel_router

from src.generate_reports.trade_turnover.make_excel import trade_turnover_excel_report_router
from src.generate_reports.trade_turnover.graphics_for_pdf import trade_turnover_pdf_router

from src.generate_reports.turnover_by_objects.make_excel import trade_turnover_for_various_objects_excel_router
from src.generate_reports.turnover_by_objects.graphics_for_pdf import trade_turnover_for_various_objects_pdf_router

from src.generate_reports.forecasting_losses.make_excel import forecasting_losses_excel_router
from src.generate_reports.forecasting_losses.graphics_for_pdf import forecasting_losses_pdf_router

from src.generate_reports.inventory.graphics_for_pdf import inventory_pdf_router
from src.generate_reports.inventory.make_excel import inventory_excel_router

from src.generate_reports.foodcost_of_products_storehouse.graphics_for_pdf import foodcost_of_products_storehouse_pdf_router
from src.generate_reports.foodcost_of_products_storehouse.make_excel import foodcost_of_products_storehouse_excel_router

from src.generate_reports.foodcost_of_products_dishes.make_excel import foodcost_of_products_dishes_excel_router
from src.generate_reports.foodcost_of_products_dishes.graphics_for_pdf import foodcost_of_products_dishes_pdf_router

from src.mailing.notifications.keyboards import get_action_report_markup, get_report_markup, get_format_markup



subscribe_notifications = Router()


@subscribe_notifications.callback_query(F.data == 'generate_report')
async def handle_generate_report(callback_query: CallbackQuery):
    """Обработчик для кнопки 'Сформировать отчёт'"""
    logging.info("Обработчик generate_report вызван")
    await callback_query.answer("Выберите тип отчёта:")
    await callback_query.message.answer(
        "Выберите тип отчёта:",
        reply_markup=get_report_markup()  # Show report selection keyboard
    )


@subscribe_notifications.callback_query(F.data.startswith('report_'))
async def handle_report_selection(callback_query: CallbackQuery):
    """Обработчик для выбора типа отчёта"""
    # Убираем "report_" из callback_data, чтобы получить чистое имя отчёта
    report_type = callback_query.data.replace("report_", "", 1)
    logging.info(f"Выбран тип отчёта: {report_type}")

    # Уведомляем пользователя о выборе
    await callback_query.answer(f"Вы выбрали отчёт: {report_type}")

    # Отправляем клавиатуру для выбора действия (сформировать отчёт сейчас или подписаться на рассылку)
    await callback_query.message.answer(
        "Выберите действие:",
        reply_markup=get_action_report_markup(report_type)  # Генерация клавиатуры для выбора действия
    )


# Допустимые типы отчётов
TEXT_REPORT_TYPES = {
    "text_report_revenue", "text_report_losses", "text_report_purchases",
    "text_report_food_cost", "text_report_turnover", "text_report_antitheft"
}

@subscribe_notifications.callback_query(F.data.startswith(tuple(TEXT_REPORT_TYPES)))
async def report_handler(callback: CallbackQuery):
    """Обработчик для текстовых и файловых отчётов, отправляет заглушку 'В процессе'"""
    await callback.message.answer("В процессе...")
    await callback.answer()  # Закрываем всплывающее уведомление

@subscribe_notifications.callback_query(F.data.startswith('generate_now_'))
async def handle_generate_now(callback_query: CallbackQuery):
    """Обработчик для выбора 'Сформировать отчёт сейчас'"""
    report_type = callback_query.data.replace("generate_now_", "", 1)
    logging.info(f"Пользователь выбрал сформировать отчёт сейчас для типа: {report_type}")

    # Уведомляем пользователя
    await callback_query.answer(f"Вы выбрали сформировать отчёт сейчас для типа: {report_type}")

    # Отправляем клавиатуру для выбора формата отчёта (PDF или Excel)
    await callback_query.message.answer(
        "Выберите формат отчёта:",
        reply_markup=get_format_markup(report_type)  # Генерация клавиатуры для выбора формата
    )


@subscribe_notifications.callback_query(F.data.startswith('subscribe_'))
async def handle_subscribe(callback_query: CallbackQuery, state: FSMContext):
    """Обработчик для выбора 'Подписаться на рассылку'"""
    # Извлекаем тип отчёта из callback_data
    report_type = callback_query.data.replace("subscribe_", "", 1)
    logging.info(f"Пользователь выбрал подписаться на рассылку для типа: {report_type}")

    # Сохраняем тип отчёта в состоянии (FSM)
    await state.update_data(report_type=report_type)

    # Уведомляем пользователя
    await callback_query.answer(f"Вы выбрали подписаться на рассылку для типа: {report_type}")

    # Перекидываем пользователя на выбор периодичности рассылки
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Ежедневно", callback_data="sub_daily")],
        [types.InlineKeyboardButton(text="По будням (Пн-Пт)", callback_data="sub_workdays")],
        [types.InlineKeyboardButton(text="Еженедельно", callback_data="sub_weekly")],
        [types.InlineKeyboardButton(text="Ежемесячно", callback_data="sub_monthly")]
    ])
    await callback_query.message.answer("Выберите периодичность рассылки:", reply_markup=keyboard)


@subscribe_notifications.callback_query(F.data == 'report_revenue_analysis')
async def handle_revenue_analysis(callback_query: CallbackQuery):
    """Обработчик для отчета по анализу выручки"""
    await callback_query.answer("Вы выбрали отчет по анализу выручки.")
    await callback_query.message.answer(
        "Выберите формат отчета:",
        reply_markup=get_format_markup('revenue_analysis')
    )


@subscribe_notifications.callback_query(F.data == 'report_turnover')
async def handle_turnover(callback_query: CallbackQuery):
    """Обработчик для отчета по товарообороту"""
    await callback_query.answer("Вы выбрали отчет по товарообороту.")
    await callback_query.message.answer(
        "Выберите формат отчета:",
        reply_markup=get_format_markup('turnover')
    )


@subscribe_notifications.callback_query(F.data == 'report_turnover_by_objects')
async def handle_turnover_by_objects(callback_query: CallbackQuery):
    """Обработчик для отчета по товарообороту для различных объектов"""
    await callback_query.answer("Вы выбрали отчет по товарообороту для различных объектов.")
    await callback_query.message.answer(
        "Выберите формат отчета:",
        reply_markup=get_format_markup('turnover_by_objects')
    )


@subscribe_notifications.callback_query(F.data == 'report_loss_forecast')
async def handle_loss_forecast(callback_query: CallbackQuery):
    """Обработчик для отчета по прогнозированию потерь для товаров"""
    await callback_query.answer("Вы выбрали отчет по прогнозированию потерь для товаров.")
    await callback_query.message.answer(
        "Выберите формат отчета:",
        reply_markup=get_format_markup('loss_forecast')
    )


@subscribe_notifications.callback_query(F.data == 'report_inventory')
async def handle_inventory(callback_query: CallbackQuery):
    """Обработчик для отчета по инвентаризации на складе"""
    await callback_query.answer("Вы выбрали отчет по инвентаризации на складе.")
    await callback_query.message.answer(
        "Выберите формат отчета:",
        reply_markup=get_format_markup('inventory')
    )


@subscribe_notifications.callback_query(F.data == 'report_food_cost')
async def handle_food_cost(callback_query: CallbackQuery):
    """Обработчик для отчета по себестоимости продуктов"""
    await callback_query.answer("Вы выбрали отчет по себестоимости продуктов.")
    await callback_query.message.answer(
        "Выберите формат отчета:",
        reply_markup=get_format_markup('food_cost')
    )


@subscribe_notifications.callback_query(F.data == 'report_food_cost_dynamics')
async def handle_food_cost_dynamics(callback_query: CallbackQuery):
    """Обработчик для отчета по себестоимости продуктов с изменениями"""
    await callback_query.answer("Вы выбрали отчет по себестоимости продуктов с изменениями.")
    await callback_query.message.answer(
        "Выберите формат отчета:",
        reply_markup=get_format_markup('food_cost_dynamics')
    )


def setup_routers_select_reports():
    subscribe_notifications.include_router(analys_revenue_excel_router)
    subscribe_notifications.include_router(trade_turnover_excel_report_router)
    subscribe_notifications.include_router(trade_turnover_for_various_objects_excel_router)
    subscribe_notifications.include_router(forecasting_losses_excel_router)
    subscribe_notifications.include_router(inventory_excel_router)
    subscribe_notifications.include_router(foodcost_of_products_storehouse_excel_router)
    subscribe_notifications.include_router(foodcost_of_products_dishes_excel_router)

    subscribe_notifications.include_router(analys_revenue_pdf_router)
    subscribe_notifications.include_router(trade_turnover_pdf_router)
    subscribe_notifications.include_router(trade_turnover_for_various_objects_pdf_router)
    subscribe_notifications.include_router(forecasting_losses_pdf_router)
    subscribe_notifications.include_router(inventory_pdf_router)
    subscribe_notifications.include_router(foodcost_of_products_storehouse_pdf_router)
    subscribe_notifications.include_router(foodcost_of_products_dishes_pdf_router)