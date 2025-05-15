import os
from typing import Union, List
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# Логгер
import logging

logging.basicConfig(level=logging.INFO)


def safe_float(value):
    """Преобразует значение в тип float, если возможно, или возвращает 0."""
    try:
        return float(value) if value else 0
    except ValueError:
        return 0


def format_percent(val):
    """Форматирует значение в процентный формат с двумя знаками после запятой."""
    try:
        return f"{float(val):.2f}%" if val is not None else "—"
    except:
        return "—"


def write_off_parameters_create_pdf_report(data: Union[List[dict], dict]) -> BytesIO:
    """Создаёт PDF отчёт по списаниям товаров с единым стилем оформления."""

    if isinstance(data, list):
        if not data:
            raise ValueError("Пустой список данных")
        data = data[0]

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4))

    # Регистрация шрифта
    font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    elements = []
    styles = getSampleStyleSheet()

    # Заголовок
    title_style = ParagraphStyle(
        name='TitleStyle',
        fontName='DejaVuSans',
        fontSize=16,
        alignment=1,
        textColor=colors.black
    )
    elements.append(Paragraph("Списания по статьям", title_style))
    elements.append(Spacer(1, 12))

    # Заголовок таблицы
    table_data = [["Статья списания", "Сумма", "Динамика неделя", "Динамика месяц", "Динамика год"]]

    for item in data.get("data", []):
        if (safe_float(item.get('write_off')) == 0 and
            safe_float(item.get('write_off_week')) == 0 and
            safe_float(item.get('write_off_month')) == 0 and
            safe_float(item.get('write_off_year')) == 0):
            continue

        write_off = safe_float(item.get('write_off'))
        table_data.append([
            item.get("label", "—"),
            f"{write_off:,.2f}" if write_off != 0 else "—",
            format_percent(item.get('write_off_dynamics_week')),
            format_percent(item.get('write_off_dynamics_month')),
            format_percent(item.get('write_off_dynamics_year'))
        ])

    table = Table(table_data, colWidths=[3 * inch] + [1.5 * inch] * 4)

    # Общий стиль, как в inventory-отчёте
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

    # Цвета текста для динамики: зелёный (+) / красный (–)
    for i, row in enumerate(table_data[1:], start=1):
        week = safe_float(row[2].replace('%', '').replace('—', '0'))
        month = safe_float(row[3].replace('%', '').replace('—', '0'))
        year = safe_float(row[4].replace('%', '').replace('—', '0'))

        if week > 0:
            style.append(('TEXTCOLOR', (2, i), (2, i), colors.green))
        elif week < 0:
            style.append(('TEXTCOLOR', (2, i), (2, i), colors.red))

        if month > 0:
            style.append(('TEXTCOLOR', (3, i), (3, i), colors.green))
        elif month < 0:
            style.append(('TEXTCOLOR', (3, i), (3, i), colors.red))

        if year > 0:
            style.append(('TEXTCOLOR', (4, i), (4, i), colors.green))
        elif year < 0:
            style.append(('TEXTCOLOR', (4, i), (4, i), colors.red))

    table.setStyle(TableStyle(style))
    elements.append(table)
    elements.append(Spacer(1, 12))

    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer
