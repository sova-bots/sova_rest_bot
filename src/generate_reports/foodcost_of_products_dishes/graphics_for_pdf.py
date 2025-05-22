import json
import logging
import os

import seaborn as sns
import matplotlib.pyplot as plt
from aiogram import Router, F, types
from aiogram.handlers import callback_query
from aiogram.types import Message, FSInputFile, CallbackQuery, BufferedInputFile
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Image, Paragraph
from reportlab.lib.pagesizes import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import KeepTogether  # Добавьте этот импорт

import pandas as pd

# Helper functions (same as before)
def get_first_non_null(*values):
    for value in values:
        if value is not None:
            return value
    return "-"

def calculate_percentage_change(old_value, new_value):
    if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)) and old_value != 0:
        return round(((new_value - old_value) / old_value) * 100, 2)
    return None

def calculate_monthly_differences(store):
    diff_price = store.get("food_cost_dynamics_week")
    diff_price2 = store.get("food_cost_dynamics_month")
    diff_price3 = store.get("food_cost_dynamics_year")

    diff_price_1 = get_first_non_null(diff_price, diff_price2, diff_price3)

    if isinstance(diff_price2, (int, float)) and isinstance(diff_price, (int, float)):
        diff_price_1_week = calculate_percentage_change(diff_price, diff_price2)
    else:
        diff_price_1_week = "-"

    if isinstance(diff_price3, (int, float)) and isinstance(diff_price2, (int, float)):
        diff_price_2_month = calculate_percentage_change(diff_price2, diff_price3)
    else:
        diff_price_2_month = "-"

    return diff_price_1, diff_price_1_week, diff_price_2_month

def safe_format(value):
    if value is None:
        return "-"
    if isinstance(value, (int, float)):
        return f"{value:,.2f}%"  # Add percentage formatting
    return str(value)

# Function to create the stacked bar chart for each product
def create_stacked_bar_chart(data):
    products = []
    day_prices = []
    month_prices = []
    year_prices = []

    # Collect data for each product
    for product in data["data"]:
        products.append(product["label"])
        day_price = product.get("food_cost_dynamics_day", 0)
        month_price = product.get("food_cost_dynamics_month", 0)
        year_price = product.get("food_cost_dynamics_year", 0)

        day_prices.append(day_price if isinstance(day_price, (int, float)) else 0)
        month_prices.append(month_price if isinstance(month_price, (int, float)) else 0)
        year_prices.append(year_price if isinstance(year_price, (int, float)) else 0)

    # Create a DataFrame for better handling
    df = pd.DataFrame({
        "Product": products,
        "Day": day_prices,
        "Month": month_prices,
        "Year": year_prices
    })

    # Create subplots for each time period
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)

    # Plot Day prices
    df.plot(kind="bar", x="Product", y="Day", ax=axes[0], color="skyblue", legend=False)
    axes[0].set_title("Цены за день", fontsize=14, family='DejaVuSans')  # Title in Russian
    axes[0].set_ylabel("Цена", fontsize=12, family='DejaVuSans')
    axes[0].tick_params(axis="x", rotation=45)

    # Plot Month prices
    df.plot(kind="bar", x="Product", y="Month", ax=axes[1], color="lightgreen", legend=False)
    axes[1].set_title("Цены за месяц", fontsize=14, family='DejaVuSans')  # Title in Russian
    axes[1].tick_params(axis="x", rotation=45)

    # Plot Year prices
    df.plot(kind="bar", x="Product", y="Year", ax=axes[2], color="salmon", legend=False)
    axes[2].set_title("Цены за год", fontsize=14, family='DejaVuSans')  # Title in Russian
    axes[2].tick_params(axis="x", rotation=45)

    # Adjust layout
    plt.tight_layout()

    # Save the plot as an image file
    plot_image_path = "stacked_bar_chart.png"
    plt.savefig(plot_image_path, format="png")
    plt.close()

    return plot_image_path

def create_pdf_report(data, output_file="food_cost_dish_report.pdf"):
    pdfmetrics.registerFont(TTFont('DejaVuSans',
                                   r"C:\\WORK\\sova_rest_bot\\sova_rest_bot-master\\src\\basic\\revenue_analysis\\DejaVuSans.ttf"))
    doc = SimpleDocTemplate(output_file, pagesize=landscape(letter))  # Set to landscape format

    headers = [
        "Продукт", "Фудкость", "Динамика неделя",
        "Динамика месяц", "Динамика год"
    ]

    style_table_header = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                     ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                     ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                     ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
                                     ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                                     ('TOPPADDING', (0, 0), (-1, 0), 10),
                                     ('FONTSIZE', (0, 0), (-1, -1), 6),
                                     ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                     ])

    table_data = [headers]
    sorted_data = sorted(data["data"], key=lambda x: x["food_cost"], reverse=True)

    elements = []  # Accumulate both table and graph elements here

    # Create table data
    for product in sorted_data:
        food_cost_1, food_cost_1_week, food_cost_2_month = calculate_monthly_differences(product)

        row = [
            product["label"],
            safe_format(product['food_cost']),
            safe_format(food_cost_1_week),
            safe_format(food_cost_1),
            safe_format(food_cost_2_month),
        ]
        table_data.append(row)

    # Add table after the title
    header_height = 0.4 * inch
    row_height = 0.3 * inch

    colWidths = [
        1.7 * inch, 0.9 * inch, 1 * inch, 1.5 * inch, 1.5 * inch
    ]

    row_heights = [header_height] + [row_height] * (len(table_data) - 1)

    table = Table(table_data, colWidths=colWidths, rowHeights=row_heights)
    table.setStyle(style_table_header)

    elements.append(Spacer(1, 12))  # Add space before the table

    # Create the stacked bar chart
    bar_chart_image = create_stacked_bar_chart(data)
    img = Image(bar_chart_image, width=6 * inch, height=4 * inch)

    # Use KeepTogether to ensure the table and graph stay on the same page
    elements.append(KeepTogether([table, Spacer(1, 12), img]))

    doc.build(elements)

    print(f"PDF-файл успешно сохранен: {output_file}")


# Define router
foodcost_of_products_dishes_pdf_router = Router()

# Helper function to load JSON data
def load_json_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except Exception as e:
        print(f"Ошибка загрузки данных JSON из {file_path}: {e}")
        return None

# Helper function to create PDF report
def create_pdf_report(data, output_file="food_cost_dish_report.pdf"):
    pdfmetrics.registerFont(TTFont('DejaVuSans', r"C:\WORK\sova_rest_bot\sova_rest_bot-master\src\basic\revenue_analysis\DejaVuSans.ttf"))
    doc = SimpleDocTemplate(output_file, pagesize=landscape(letter))  # Set to landscape format

    headers = [
        "Продукт", "Фудкость", "Динамика неделя",
        "Динамика месяц", "Динамика год"
    ]

    style_table_header = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                     ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                     ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                     ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
                                     ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                                     ('TOPPADDING', (0, 0), (-1, 0), 10),
                                     ('FONTSIZE', (0, 0), (-1, -1), 6),
                                     ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                     ])

    table_data = [headers]
    sorted_data = sorted(data["data"], key=lambda x: x["food_cost"], reverse=True)

    elements = []

    for product in sorted_data:
        food_cost_1, food_cost_1_week, food_cost_2_month = calculate_monthly_differences(product)

        row = [
            product["label"],
            safe_format(product['food_cost']),
            safe_format(food_cost_1_week),
            safe_format(food_cost_1),
            safe_format(food_cost_2_month),
        ]
        table_data.append(row)

    header_height = 0.4 * inch
    row_height = 0.3 * inch
    colWidths = [1.7 * inch, 0.9 * inch, 1 * inch, 1.5 * inch, 1.5 * inch]
    row_heights = [header_height] + [row_height] * (len(table_data) - 1)

    table = Table(table_data, colWidths=colWidths, rowHeights=row_heights)
    table.setStyle(style_table_header)

    elements.append(Spacer(1, 12))  # Add space before the table

    bar_chart_image = create_stacked_bar_chart(data)
    img = Image(bar_chart_image, width=6 * inch, height=4 * inch)

    elements.append(KeepTogether([table, Spacer(1, 12), img]))

    doc.build(elements)
    print(f"PDF-файл успешно сохранен: {output_file}")
    return output_file

def load_revenue_data(filepath: str) -> dict:
    """Загружает данные из JSON-файла."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Ошибка при чтении файла {filepath}: {e}")
        return {}


# Function to handle report generation
@foodcost_of_products_dishes_pdf_router.callback_query(F.data =="format_pdf_food_cost")
async def generate_report(callback_query: types.CallbackQuery):
    """Обработчик для кнопки 'Сформировать PDF отчёт'."""
    # Отвечаем на callback_query, чтобы убрать "часики" у кнопки
    await callback_query.answer("Формирую PDF отчёт...")

    # Извлекаем тип отчёта из callback_data
    report_type = callback_query.data.split("_")[-1]

    # Читаем данные из JSON-файла
    file_path = r'sova_rest_bot-new_structure/resources/jsons_for_test/food-cost-dish_server_data_example.json'
    revenue_data = load_revenue_data(file_path)

    if not revenue_data:
        await callback_query.message.answer("Ошибка при загрузке данных для отчёта.")
        return

    # Генерация графика
    try:
        bar_chart_image = create_stacked_bar_chart(revenue_data)
    except Exception as e:
        logging.error(f"Ошибка при создании графика: {e}")
        await callback_query.message.answer("Ошибка при создании графика для отчёта.")
        return

    # Создание PDF
    try:
        pdf_file = create_pdf_report(revenue_data)  # This generates the PDF and saves it to the disk
    except Exception as e:
        logging.error(f"Ошибка при создании PDF: {e}")
        await callback_query.message.answer("Ошибка при создании PDF-отчёта.")
        return

    # Отправка PDF пользователю
    try:
        # Отправляем PDF-файл
        await callback_query.message.answer_document(
            document=FSInputFile(pdf_file),
            caption=f"Ваш отчёт по анализу выручки (тип: {report_type}):"
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке PDF: {e}")
        await callback_query.message.answer("Ошибка при отправке отчёта.")



