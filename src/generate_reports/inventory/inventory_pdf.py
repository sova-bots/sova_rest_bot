import os
from typing import Union, Dict, List
from io import BytesIO
import json
import logging
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont

# Создание логгера
logging.basicConfig(level=logging.INFO)

def safe_float(value):
    """Преобразует значение в тип float, если возможно, или возвращает 0."""
    try:
        return float(value) if value else 0
    except ValueError:
        return 0

def inventory_parameters_create_pdf_report(data: Union[List[dict], dict]) -> BytesIO:
    """Создаёт PDF отчёт по данным инвентаризации товаров."""
    if isinstance(data, list):
        if not data:
            raise ValueError("Пустой список данных")
        data = data[0]

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4))

    font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='TitleStyle', fontName='DejaVuSans', fontSize=16, alignment=1)
    elements.append(Paragraph("Инвентаризация по складам", title_style))
    elements.append(Spacer(1, 12))

    # Удалена колонка "Себестоимость"
    table_data = [["Магазин", "Недостача", "Недостача (% от с/с)", "Излишки", "Излишки (% от с/с)"]]
    for store in data.get("data", []):
        table_data.append([
            store.get("label", ""),
            f"{safe_float(store.get('shortage')):,.2f}",
            f"{safe_float(store.get('shortage_percent')):,.2f}%",
            f"{safe_float(store.get('surplus')):,.2f}",
            f"{safe_float(store.get('surplus_percent')):,.2f}%"
        ])

    # Обновлённая ширина столбцов: 1 + 4
    table = Table(table_data, colWidths=[3 * inch] + [1.5 * inch] * 4)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]

    for i, store in enumerate(data.get("data", []), start=1):
        if safe_float(store.get('shortage_percent')) > 2:
            style.append(('TEXTCOLOR', (2, i), (2, i), colors.red))
        if safe_float(store.get('surplus_percent')) > 3:
            style.append(('TEXTCOLOR', (4, i), (4, i), colors.green))

    table.setStyle(TableStyle(style))
    elements.append(table)
    elements.append(Spacer(1, 12))

    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer


