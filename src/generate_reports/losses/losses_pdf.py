import os
from typing import Union, List, Dict
from io import BytesIO
import logging
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

logging.basicConfig(level=logging.INFO)

def safe_float(value):
    try:
        return float(value) if value else 0.0
    except ValueError:
        return 0.0

def losses_parameters_create_pdf_report(data: Union[List[Dict], Dict]) -> BytesIO:
    if isinstance(data, list):
        if not data:
            raise ValueError("Пустой список данных")
        data = data[0]

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4))

    # Регистрируем шрифт DejaVuSans
    font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    elements = []
    styles = getSampleStyleSheet()

    # Используем DejaVuSans для заголовка
    title_style = ParagraphStyle(name='TitleStyle', fontName='DejaVuSans', fontSize=14, alignment=1)
    elements.append(Paragraph("Потери по товарам", title_style))
    elements.append(Spacer(1, 12))

    # Заголовок таблицы (с разбиением на две строки)
    headers = [
        "Товар",
        "Средняя цена\nпрошлый месяц",
        "Средняя цена\nпрошлая неделя",
        "Средняя цена\nтекущий месяц",
        "Средняя цена\nтекущая неделя",
        "Потери\n(прошлый месяц \n к позапрошлому)",
        "Потери\n(прошлая неделя \n к позапрошлой)",
        "Потери\n(текущий месяц \n к прошлому)"
    ]
    table_data = [headers]

    totals = [0.0] * 7

    for item in data.get("data", []):
        row = [
            item.get("label", ""),
            f"{safe_float(item.get('avg_price_last_month')):,.2f}",
            f"{safe_float(item.get('avg_price_last_week')):,.2f}",
            f"{safe_float(item.get('avg_price_current_month')):,.2f}" if item.get("avg_price_current_month") else "-",
            f"{safe_float(item.get('avg_price_current_week')):,.2f}",
            f"{safe_float(item.get('losses_last_month_to_month_before_last')):,.2f}",
            f"{safe_float(item.get('losses_last_week_to_week_before_last')):,.2f}",
            f"{safe_float(item.get('losses_current_month_to_last')):,.2f}"
        ]
        table_data.append(row)

        totals[0] += safe_float(item.get('avg_price_last_month'))
        totals[1] += safe_float(item.get('avg_price_last_week'))
        totals[2] += safe_float(item.get('avg_price_current_month'))
        totals[3] += safe_float(item.get('avg_price_current_week'))
        totals[4] += safe_float(item.get('losses_last_month_to_month_before_last'))
        totals[5] += safe_float(item.get('losses_last_week_to_week_before_last'))
        totals[6] += safe_float(item.get('losses_current_month_to_last'))

    totals_row = ["Итого:"] + [f"{value:,.2f}" for value in totals]
    table_data.append(totals_row)

    # Увеличим ширину первого столбца
    table = Table(table_data, colWidths=[2.5 * inch] + [1.2 * inch] * 7)

    style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),  # Используем DejaVuSans
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'DejaVuSans')  # Для итога тоже используем DejaVuSans
    ]

    for i, item in enumerate(data.get("data", []), start=1):
        if safe_float(item.get('losses_current_month_to_last')) > 1000:
            style.append(('TEXTCOLOR', (7, i), (7, i), colors.red))
        if safe_float(item.get('avg_price_current_month')) > 500:
            style.append(('TEXTCOLOR', (3, i), (3, i), colors.green))

    table.setStyle(TableStyle(style))
    elements.append(table)
    elements.append(Spacer(1, 12))

    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer


def losses_only_negative_create_pdf_report(data: Union[List[Dict], Dict]) -> BytesIO:
    if isinstance(data, list):
        if not data:
            raise ValueError("Пустой список данных")
        data = data[0]

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4))

    # Регистрируем шрифт DejaVuSans
    font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    elements = []
    styles = getSampleStyleSheet()

    # Используем DejaVuSans для заголовка
    title_style = ParagraphStyle(name='TitleStyle', fontName='DejaVuSans', fontSize=14, alignment=1)
    elements.append(Paragraph("Потери по товарам", title_style))
    elements.append(Spacer(1, 12))

    # Заголовок таблицы (с разбиением на две строки)
    headers = [
        "Товар",
        "Средняя цена\nпрошлый месяц",
        "Средняя цена\nпрошлая неделя",
        "Средняя цена\nтекущий месяц",
        "Средняя цена\nтекущая неделя",
        "Потери\n(прошлый месяц \n к позапрошлому)",
        "Потери\n(прошлая неделя \n к позапрошлой)",
        "Потери\n(текущий месяц \n к прошлому)"
    ]
    table_data = [headers]

    totals = [0.0] * 7

    for item in data.get("data", []):
        losses_last_month = safe_float(item.get('losses_last_month_to_month_before_last'))
        losses_last_week = safe_float(item.get('losses_last_week_to_week_before_last'))
        losses_current_month = safe_float(item.get('losses_current_month_to_last'))

        # Проверяем, есть ли хотя бы одна потеря больше нуля
        if losses_last_month > 0 or losses_last_week > 0 or losses_current_month > 0:
            row = [
                item.get("label", ""),
                f"{safe_float(item.get('avg_price_last_month')):,.2f}",
                f"{safe_float(item.get('avg_price_last_week')):,.2f}",
                f"{safe_float(item.get('avg_price_current_month')):,.2f}" if item.get("avg_price_current_month") else "-",
                f"{safe_float(item.get('avg_price_current_week')):,.2f}",
                f"{losses_last_month:,.2f}",
                f"{losses_last_week:,.2f}",
                f"{losses_current_month:,.2f}"
            ]
            table_data.append(row)

            totals[0] += safe_float(item.get('avg_price_last_month'))
            totals[1] += safe_float(item.get('avg_price_last_week'))
            totals[2] += safe_float(item.get('avg_price_current_month'))
            totals[3] += safe_float(item.get('avg_price_current_week'))
            totals[4] += losses_last_month
            totals[5] += losses_last_week
            totals[6] += losses_current_month

    totals_row = ["Итого:"] + [f"{value:,.2f}" for value in totals]
    table_data.append(totals_row)

    # Увеличим ширину первого столбца
    table = Table(table_data, colWidths=[2.5 * inch] + [1.2 * inch] * 7)

    style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),  # Используем DejaVuSans
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'DejaVuSans')  # Для итога тоже используем DejaVuSans
    ]

    for i, item in enumerate(data.get("data", []), start=1):
        if safe_float(item.get('losses_current_month_to_last')) > 1000:
            style.append(('TEXTCOLOR', (7, i), (7, i), colors.red))
        if safe_float(item.get('avg_price_current_month')) > 500:
            style.append(('TEXTCOLOR', (3, i), (3, i), colors.green))

    table.setStyle(TableStyle(style))
    elements.append(table)
    elements.append(Spacer(1, 12))

    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer
