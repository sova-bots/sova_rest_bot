import json
import logging
import os

from aiogram.filters import Command

from aiogram import Router, types, F
from aiogram.types import FSInputFile
from reportlab.lib.pagesizes import letter, landscape, inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import pandas as pd

foodcost_of_products_storehouse_pdf_router = Router()

# Helper functions (no change from previous code)
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
    diff_price = store.get("food_cost_dynamics_day")
    diff_price2 = store.get("food_cost_dynamics_week")
    diff_price3 = store.get("food_cost_dynamics_month")

    diff_price_1 = get_first_non_null(diff_price, diff_price2, diff_price3)

    if isinstance(diff_price2, (int, float)) and isinstance(diff_price, (int, float)):
        diff_price_1_day = calculate_percentage_change(diff_price, diff_price2)
    else:
        diff_price_1_day = "-"

    if isinstance(diff_price3, (int, float)) and isinstance(diff_price2, (int, float)):
        diff_price_2_week = calculate_percentage_change(diff_price2, diff_price3)
    else:
        diff_price_2_week = "-"

    return diff_price_1, diff_price_1_day, diff_price_2_week

def safe_format(value):
    if value is None:
        return "-"
    if isinstance(value, (int, float)):
        return f"{value:,.2f}%"  # Add percentage formatting
    return str(value)

def create_pdf_report(data, output_file="food_cost_server_report.pdf"):
    # Create PDF document with landscape (horizontal) orientation
    doc = SimpleDocTemplate(output_file, pagesize=landscape(letter))
    elements = []

    pdfmetrics.registerFont(TTFont('DejaVuSans',
                                   r"C:\\WORK\\sova_rest_bot\\sova_rest_bot-master\\src\\basic\\revenue_analysis\\DejaVuSans.ttf"))

    # Title of the report
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name='TitleStyle',
        fontName='DejaVuSans',  # Set the font to DejaVuSans
        fontSize=14,  # Adjust font size if needed
        alignment=1,  # Center the title
        spaceAfter=12  # Space after title
    )

    # Title of the report
    title = Paragraph("Себестоимость точек", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))  # Space after title

    # Headers for the table
    headers = [
        "Название", "Фудкост", "Динамика день", "Динамика неделя", "Динамика месяц"
    ]

    # Prepare table data
    table_data = [headers]

    for product in data["data"]:
        food_cost_1, food_cost_1_day, food_cost_2_week = calculate_monthly_differences(product)

        row = [
            product["label"],
            safe_format(product['food_cost']),
            safe_format(food_cost_1_day),
            safe_format(food_cost_1),
            safe_format(food_cost_2_week),
        ]
        table_data.append(row)

    # Set fixed column widths in inches
    col_widths = [2 * inch, 1.3 * inch, 1.3 * inch, 1.2 * inch, 1.2 * inch]  # Example: Fixed width for each column in inches

    # Create the table with fixed column widths
    table = Table(table_data, colWidths=col_widths)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.yellow),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # Smaller font size
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),  # Reduced bottom padding
        ('TOPPADDING', (0, 0), (-1, -1), 3),  # Reduced top padding
        ('LEFTPADDING', (0, 0), (-1, -1), 3),  # Reduced left padding
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),  # Reduced right padding
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)

    # Prepare the data for the bar chart
    labels = []
    values_day = []
    values_week = []
    values_month = []

    for product in data["data"]:
        food_cost_1, food_cost_1_day, food_cost_2_week = calculate_monthly_differences(product)

        labels.append(product["label"])
        values_day.append(food_cost_1_day if isinstance(food_cost_1_day, (int, float)) else 0)
        values_week.append(food_cost_2_week if isinstance(food_cost_2_week, (int, float)) else 0)
        values_month.append(food_cost_1 if isinstance(food_cost_1, (int, float)) else 0)

    # Create the bar chart with Seaborn
    df = pd.DataFrame({
        'Product': labels,
        'Day': values_day,
        'Week': values_week,
        'Month': values_month
    })

    # Reshape data for seaborn
    df_melted = df.melt(id_vars='Product', value_vars=['Day', 'Week', 'Month'],
                        var_name='Time Period', value_name='Price Change')

    plt.figure(figsize=(10, 6))
    sns.barplot(x='Product', y='Price Change', hue='Time Period', data=df_melted)

    # Customize the plot with Russian labels
    plt.xticks(rotation=90)
    plt.xlabel("Продукт")
    plt.ylabel("Изменение цены (%)")
    plt.title("Изменение цен с течением времени по продуктам")

    # Save the plot to a BytesIO object and add it to the PDF
    img_stream = BytesIO()
    plt.savefig(img_stream, format='png')
    img_stream.seek(0)  # Go to the beginning of the image stream
    plt.close()

    # Create an image from the plot
    from reportlab.platypus import Image
    chart_image = Image(img_stream)
    chart_image._restrictSize(5 * inch, 3 * inch)  # Adjust size if needed

    # Add chart image to the PDF
    elements.append(Spacer(1, 12))  # Space between the table and the chart
    elements.append(chart_image)

    # Build the PDF
    doc.build(elements)
    print(f"PDF-файл успешно сохранен: {output_file}")
    return output_file  # Return the file path here


def load_revenue_data(filepath: str) -> dict:
    """Загружает данные из JSON-файла."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Ошибка при чтении файла {filepath}: {e}")
        return {}


@foodcost_of_products_storehouse_pdf_router.callback_query(F.data =="format_pdf_food_cost_dynamics")
async def generate_report(callback_query: types.CallbackQuery):
    """Обработчик для кнопки 'Сформировать PDF отчёт'."""
    # Отвечаем на callback_query, чтобы убрать "часики" у кнопки
    await callback_query.answer("Формирую PDF отчёт...")

    # Извлекаем тип отчёта из callback_data
    report_type = callback_query.data.split("_")[-1]

    # Читаем данные из JSON-файла
    file_path = r'C:\\WORK\\sova_rest_bot\\sova_rest_bot-master\\files\\jsons_for_reports\\food-cost-dish_server_data_example.json'
    revenue_data = load_revenue_data(file_path)

    if not revenue_data:
        await callback_query.message.answer("Ошибка при загрузке данных для отчёта.")
        return

    # Создание PDF и получение пути к файлу
    try:
        pdf_file = create_pdf_report(revenue_data)  # Now returns the PDF file path
        logging.info(f"PDF файл создан по пути: {pdf_file}")
    except Exception as e:
        logging.error(f"Ошибка при создании PDF: {e}")
        await callback_query.message.answer("Ошибка при создании PDF-отчёта.")
        return

    # Отправка PDF пользователю
    try:
        # Проверка, что путь к файлу существует
        if not os.path.exists(pdf_file):
            logging.error(f"PDF файл не найден по пути: {pdf_file}")
            await callback_query.message.answer("Ошибка: PDF файл не найден.")
            return

        # Отправляем PDF-файл
        await callback_query.message.answer_document(
            document=FSInputFile(pdf_file),
            caption=f"Ваш отчёт по (тип: {report_type}):"
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке PDF: {e}")
        await callback_query.message.answer("Ошибка при отправке отчёта.")

