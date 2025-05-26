import json
import logging
import os
from io import BytesIO
import matplotlib.pyplot as plt
from aiogram.filters import Command
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from sympy.parsing.sympy_parser import null
import logging
from aiogram import Router, types, F
from aiogram.types import FSInputFile, BufferedInputFile, CallbackQuery

trade_turnover_for_various_objects_pdf_router = Router()

# Функция загрузки данных из JSON
def load_revenue_data(filepath: str) -> dict:
    """Загружает данные из JSON-файла."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Ошибка при чтении файла {filepath}: {e}")
        return {}


def create_pdf_with_narrow_table_and_graphs(data: dict, graph_bytes: BytesIO) -> BytesIO:
    """Создает PDF с узкой таблицей и графиком."""
    pdfmetrics.registerFont(
        TTFont('FreeSerif', r"C:\WORK\sova_rest_bot\sova_rest_bot-master\src\basic\revenue_analysis\FreeSerif.ttf"))

    title_style = ParagraphStyle(name='TitleStyle', fontName='FreeSerif', fontSize=10, alignment=1)  # Adjusted title size
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'FreeSerif'),
        ('FONTNAME', (0, 1), (-1, -1), 'FreeSerif'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 2),  # Reduced bottom padding
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -1), 'FreeSerif'),
        ('FONTSIZE', (0, 0), (-1, -1), 6),  # Further reduced font size
        ('TOPPADDING', (0, 0), (-1, -1), 2),  # Reduced padding
        ('LEFTPADDING', (0, 0), (-1, -1), 2),  # Reduced padding
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),  # Reduced padding
    ])

    # Set narrower column widths for better fitting
    col_widths = [1.5 * inch, 0.8 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch,
                  0.9 * inch, 0.9 * inch]

    # Prepare buffer for PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Title
    title = Paragraph("Себестоимость различных товаров", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Data for table
    headers = [
        "Заведение", "Расход в день", "Оборачиваемость", "Динамика за неделю",
        "Динамика за месяц", "За год", "За неделю", "За месяц",
        "Оборачиваемость за год", "Остаток на конец периода"
    ]

    data_for_table = []
    for item in data["data"]:
        row = [
            item["label"], item["expense_day"], item.get("turnover_in_days", ""),
            item.get("turnover_in_days_dynamic_week", ""),
            item.get("turnover_in_days_dynamic_month", ""),
            item.get("turnover_in_days_dynamic_year", ""),
            item.get("turnover_in_days_week", ""),
            item.get("turnover_in_days_month", ""),
            item.get("turnover_in_days_year", ""),
            item["remainder_end"]
        ]
        data_for_table.append(row)

    # Adding totals
    total_row = [
        data["sum"]["label"], data["sum"]["expense_day"], data["sum"].get("turnover_in_days", ""),
        data["sum"].get("turnover_in_days_dynamic_week", ""),
        data["sum"].get("turnover_in_days_dynamic_month", ""),
        data["sum"].get("turnover_in_days_dynamic_year", ""),
        data["sum"].get("turnover_in_days_week", ""),
        data["sum"].get("turnover_in_days_month", ""),
        data["sum"].get("turnover_in_days_year", ""),
        data["sum"]["remainder_end"]
    ]
    data_for_table.append(total_row)

    # Create table with narrow columns
    table = Table([headers] + data_for_table, colWidths=col_widths)

    # Apply table style
    table.setStyle(table_style)

    elements.append(table)

    # Add the graph image
    graph_image = Image(graph_bytes, width=400, height=300)
    elements.append(Spacer(1, 12))  # Add space before the image
    elements.append(graph_image)

    # Build PDF
    doc.build(elements)

    # Return PDF buffer
    buffer.seek(0)
    return buffer



# Функция для создания комбинированного графика
def create_combined_graph(data: dict) -> BytesIO:
    """Создает комбинированный график с динамикой товарооборота."""
    # Подготовка данных для графика
    labels = [item["label"] for item in data["data"]]

    # Преобразуем данные в числовые значения, если необходимо
    turnover_week = [
        float(item["turnover_in_days_week"]) if item["turnover_in_days_week"] not in [None, ''] else 0
        for item in data["data"]
    ]
    turnover_month = [
        float(item["turnover_in_days_month"]) if item["turnover_in_days_month"] not in [None, ''] else 0
        for item in data["data"]
    ]

    # Создание графика
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(labels, turnover_week, color='blue', label='Turnover Week')
    ax.barh(labels, turnover_month, left=turnover_week, color='orange', label='Turnover Month')

    ax.set_xlabel('Turnover Days')
    ax.set_title('Turnover Comparison by Week and Month')

    ax.legend()

    # Сохраняем график в BytesIO
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)  # Перемещаем в начало буфера
    plt.close()

    return buf


@trade_turnover_for_various_objects_pdf_router.callback_query(F.data == "format_pdf_turnover_by_objects")
async def handle_format_pdf_turnover_by_objects(callback_query: CallbackQuery):
    """Обработчик для кнопки 'Сформировать PDF отчёт по товарообороту для различных объектов'."""
    # Отвечаем на callback_query, чтобы убрать "часики" у кнопки
    await callback_query.answer("Формирую PDF отчёт по товарообороту для различных объектов...")

    # Извлекаем тип отчёта из callback_data
    report_type = callback_query.data.split("_")[-1]

    # Загрузка данных из JSON-файла
    filepath = r"C:\WORK\sova_rest_bot\sova_rest_bot-master\files\jsons_for_reports\turnouver-product_example.json"
    turnover_data = load_revenue_data(filepath)  # Используем ту же функцию для загрузки данных

    if not turnover_data:
        await callback_query.message.answer("Ошибка при загрузке данных для отчёта.")
        return

    # Генерация графика
    try:
        graph_bytes = create_combined_graph(turnover_data)
    except Exception as e:
        logging.error(f"Ошибка при создании графика: {e}")
        await callback_query.message.answer("Ошибка при создании графика для отчёта.")
        return

    # Создание PDF
    try:
        pdf_buffer = create_pdf_with_narrow_table_and_graphs(turnover_data, graph_bytes)
    except Exception as e:
        logging.error(f"Ошибка при создании PDF: {e}")
        await callback_query.message.answer("Ошибка при создании PDF-отчёта.")
        return

    # Отправка PDF пользователю
    try:
        # Создаём объект BufferedInputFile для отправки PDF
        input_file = BufferedInputFile(pdf_buffer.getvalue(), filename=f"turnover_by_objects_{report_type}.pdf")

        # Отправляем документ пользователю
        await callback_query.message.answer_document(
            input_file,
            caption=f"Ваш отчёт по товарообороту для различных объектов (тип: {report_type}):"
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке PDF: {e}")
        await callback_query.message.answer("Ошибка при отправке отчёта.")