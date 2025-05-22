from aiogram import types
from io import BytesIO
import json
import logging
import matplotlib.pyplot as plt
from aiogram.types import BufferedInputFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from aiogram import Router, F

inventory_pdf_router = Router()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Function to safely convert values to float
def safe_float(value):
    try:
        return float(value) if value else 0
    except ValueError:
        return 0

# Function to generate combined graph
def create_combined_graph(data):
    labels = [store["label"] for store in data["data"]]
    shortage = [safe_float(store.get("shortage", 0)) for store in data["data"]]
    surplus = [safe_float(store.get("surplus", 0)) for store in data["data"]]

    fig = plt.figure(figsize=(16, 8))
    ax = fig.add_subplot(111)

    ax.barh(labels, shortage, label="Недостача", color='red', alpha=0.6)
    ax.barh(labels, surplus, label="Излишки", color='green', alpha=0.6)

    ax.set_xlabel("Сумма")
    ax.set_title("Недостача и Излишки по магазинам")
    ax.legend()

    img_bytes = BytesIO()
    plt.savefig(img_bytes, format='png')
    plt.close()

    img_bytes.seek(0)
    return img_bytes

# Function to generate PDF with table and graphs
def create_pdf_with_table_and_graphs(data, graph_bytes):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)

    pdfmetrics.registerFont(
        TTFont('FreeSerif', r"C:\WORK\sova_rest_bot\sova_rest_bot-master\src\basic\trade_turnover\FreeSerif.ttf"))

    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='TitleStyle', fontName='FreeSerif', fontSize=16, alignment=1)
    title = Paragraph("Инвертаризация товаров", title_style)
    elements.append(title)

    elements.append(Spacer(1, 12))

    table_data = [["Магазин", "Недостача", "Недостача (%)", "Излишки", "Излишки (%)", "Себестоимость"]]
    for store in data["data"]:
        shortage = safe_float(store.get('shortage', 0))
        shortage_percent = safe_float(store.get('shortage_percent', 0))
        surplus = safe_float(store.get('surplus', 0))
        surplus_percent = safe_float(store.get('surplus_percent', 0))
        cost_price = safe_float(store.get('cost_price', 0))

        table_data.append([store["label"],
                           f"{shortage:,.2f}",
                           f"{shortage_percent:,.2f}%",
                           f"{surplus:,.2f}",
                           f"{surplus_percent:,.2f}%",
                           f"{cost_price:,.2f}"])

    table = Table(table_data, colWidths=[2.5 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch, 1.6 * inch])

    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'FreeSerif'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]

    for i, store in enumerate(data["data"], start=1):
        shortage_percent = safe_float(store.get('shortage_percent', 0))
        surplus_percent = safe_float(store.get('surplus_percent', 0))

        if shortage_percent > 2:
            table_style.append(('TEXTCOLOR', (2, i), (2, i), colors.red))

        if surplus_percent > 3:
            table_style.append(('TEXTCOLOR', (4, i), (4, i), colors.green))

    table.setStyle(TableStyle(table_style))
    elements.append(table)

    elements.append(Spacer(1, 12))

    graph_image = Image(graph_bytes, width=6.5 * inch, height=4.5 * inch)
    elements.append(graph_image)

    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer

def load_revenue_data(filepath: str) -> dict:
    """Загружает данные из JSON-файла."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Ошибка при чтении файла {filepath}: {e}")
        return {}


# Function to handle report generation
@inventory_pdf_router.callback_query(F.data =="inventory_pdf")
async def generate_report(callback_query: types.CallbackQuery):
    """Обработчик для кнопки 'Сформировать PDF отчёт'."""
    # Отвечаем на callback_query, чтобы убрать "часики" у кнопки
    await callback_query.answer("Формирую PDF отчёт...")

    # Извлекаем тип отчёта из callback_data
    report_type = callback_query.data.split("_")[-1]

    # Читаем данные из JSON-файла
    file_path = r"C:\WORK\sova_rest_bot\sova_rest_bot-master\files\jsons_for_reports\inventory_store_example.json"
    revenue_data = load_revenue_data(file_path)

    if not revenue_data:
        await callback_query.message.answer("Ошибка при загрузке данных для отчёта.")
        return

    # Генерация графика
    try:
        graph_bytes = create_combined_graph(revenue_data)
    except Exception as e:
        logging.error(f"Ошибка при создании графика: {e}")
        await callback_query.message.answer("Ошибка при создании графика для отчёта.")
        return

    # Создание PDF
    try:
        pdf_buffer = create_pdf_with_table_and_graphs(revenue_data, graph_bytes)
    except Exception as e:
        logging.error(f"Ошибка при создании PDF: {e}")
        await callback_query.message.answer("Ошибка при создании PDF-отчёта.")
        return

    # Отправка PDF пользователю
    try:
        # Создаём объект BufferedInputFile для отправки PDF
        input_file = BufferedInputFile(pdf_buffer.getvalue(), filename=f"inventory{report_type}.pdf")

        # Отправляем документ пользователю
        await callback_query.message.answer_document(
            input_file,
            caption=f"Ваш отчёт по анализу выручки (тип: {report_type}):"
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке PDF: {e}")
        await callback_query.message.answer("Ошибка при отправке отчёта.")


