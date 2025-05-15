import os
from typing import Union, Dict, List
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


def safe_float(value):
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


def loss_forecast_create_pdf_report(data: Union[Dict, List[Dict]]) -> BytesIO:
    """Создаёт PDF-отчёт по прогнозу потерь по товарам."""
    if isinstance(data, list):
        if len(data) > 0 and isinstance(data[0], dict):
            data = data[0]
        else:
            raise ValueError("Ожидался список с одним словарём внутри.")

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4))

    font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    elements = []
    title_style = ParagraphStyle(name='TitleStyle', fontName='DejaVuSans', fontSize=14, alignment=1)
    elements.append(Paragraph("Прогноз потерь по товарам", title_style))
    elements.append(Spacer(1, 12))

    # Заголовки таблицы
    table_data = [[
        "Товар",
        "Актуальная цена",
        "Последнее изменение цены",
        "Прогноз потерь / экономии"
    ]]

    total_actual_price = 0
    total_last_change = 0
    total_forecast = 0
    total_items = 0

    for item in data.get("data", []):
        # Получаем актуальную цену (первое не null значение из avg_price_*)
        avg_prices = [
            safe_float(item.get("avg_price_one_week_ago")),
            safe_float(item.get("avg_price_two_week_ago")),
            safe_float(item.get("avg_price_three_week_ago")),
            safe_float(item.get("avg_price_four_week_ago"))
        ]
        actual_price = next((price for price in avg_prices if price is not None), None)

        # Получаем последнее изменение цены (первое не null значение из amount_*)
        amount_changes = [
            safe_float(item.get("amount_one_month_ago")),
            safe_float(item.get("amount_two_month_ago")),
            safe_float(item.get("amount_three_month_ago"))
        ]
        last_price_change = next((amount for amount in amount_changes if amount is not None), None)

        # Если есть оба значения, добавляем строку
        if actual_price is not None and last_price_change is not None:
            forecast = safe_float(item.get('forecast'))

            total_actual_price += actual_price
            total_last_change += last_price_change
            total_forecast += forecast
            total_items += 1

            row = [
                item.get("label", ""),
                f"{actual_price:,.2f}",
                f"{last_price_change:,.2f}",
                f"{forecast:,.2f}"
            ]
            table_data.append(row)

    # Добавляем итоговую строку, если есть данные
    if total_items > 0:
        total_row = [
            "Итого",
            f"{total_actual_price:,.2f}",
            f"{total_last_change:,.2f}",
            f"{total_forecast:,.2f}"
        ]
        table_data.append(total_row)

    # Создаем таблицу
    table = Table(table_data, colWidths=[3 * inch, 2 * inch, 2 * inch, 2 * inch])
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]

    if total_items > 0:
        style.extend([
            ('BACKGROUND', (0, len(table_data) - 1), (-1, len(table_data) - 1), colors.lightgrey),
            ('FONTNAME', (0, len(table_data) - 1), (-1, len(table_data) - 1), 'DejaVuSans')
        ])

    table.setStyle(TableStyle(style))
    elements.append(table)
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer


def loss_forecast_create_pdf_report(data: Union[Dict, List[Dict]]) -> BytesIO:
    """Создаёт PDF-отчёт по прогнозу потерь по товарам."""
    if isinstance(data, list):
        if len(data) > 0 and isinstance(data[0], dict):
            data = data[0]
        else:
            raise ValueError("Ожидался список с одним словарём внутри.")

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4))

    font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    elements = []
    title_style = ParagraphStyle(name='TitleStyle', fontName='DejaVuSans', fontSize=14, alignment=1)
    elements.append(Paragraph("Прогноз потерь по товарам", title_style))
    elements.append(Spacer(1, 12))

    # Заголовки таблицы
    table_data = [[
        "Товар",
        "Актуальная цена",
        "Последнее изменение цены",
        "Прогноз потерь / экономии"
    ]]

    total_actual_price = 0
    total_last_change = 0
    total_forecast = 0
    total_items = 0

    for item in data.get("data", []):
        # Получаем актуальную цену (первое не null значение из avg_price_*):
        avg_prices = [
            safe_float(item.get("avg_price_one_week_ago")),
            safe_float(item.get("avg_price_two_week_ago")),
            safe_float(item.get("avg_price_three_week_ago")),
            safe_float(item.get("avg_price_four_week_ago"))
        ]
        actual_price = next((price for price in avg_prices if price is not None), None)

        # Получаем последнее изменение цены (первое не null значение из amount_*):
        amount_changes = [
            safe_float(item.get("amount_one_month_ago")),
            safe_float(item.get("amount_two_month_ago")),
            safe_float(item.get("amount_three_month_ago"))
        ]
        last_price_change = next((amount for amount in amount_changes if amount is not None), None)

        # Получаем прогноз потерь (forecast):
        forecast = safe_float(item.get('forecast'))

        # Если есть актуальная цена, изменение цены и прогноз, и прогноз больше 0, добавляем строку
        if actual_price is not None and last_price_change is not None and forecast > 0:
            total_actual_price += actual_price
            total_last_change += last_price_change
            total_forecast += forecast
            total_items += 1

            row = [
                item.get("label", ""),
                f"{actual_price:,.2f}",
                f"{last_price_change:,.2f}",
                f"{forecast:,.2f}"
            ]
            table_data.append(row)

    # Добавляем итоговую строку, если есть данные
    if total_items > 0:
        total_row = [
            "Итого",
            f"{total_actual_price:,.2f}",
            f"{total_last_change:,.2f}",
            f"{total_forecast:,.2f}"
        ]
        table_data.append(total_row)

    # Создаем таблицу
    table = Table(table_data, colWidths=[3 * inch, 2 * inch, 2 * inch, 2 * inch])
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]

    if total_items > 0:
        style.extend([
            ('BACKGROUND', (0, len(table_data) - 1), (-1, len(table_data) - 1), colors.lightgrey),
            ('FONTNAME', (0, len(table_data) - 1), (-1, len(table_data) - 1), 'DejaVuSans')
        ])

    table.setStyle(TableStyle(style))
    elements.append(table)
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer

