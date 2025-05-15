from typing import Dict, Union, List
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os


def safe_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def create_pdf_report_for_turnover(data: Union[Dict, List[Dict]]) -> BytesIO:
    """Создаёт PDF-отчёт по оборачиваемости с новым порядком столбцов."""

    if isinstance(data, list):
        data = data[0] if data else {}

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4))

    # Подключение шрифта
    font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    elements = []
    title_style = ParagraphStyle(name='TitleStyle', fontName='DejaVuSans', fontSize=14, alignment=1)
    elements.append(Paragraph("Оборачиваемость остатков", title_style))
    elements.append(Spacer(1, 12))

    # Заголовки таблицы с выравниванием по центру
    headers = [
        Paragraph("Точка", ParagraphStyle(name='HeaderStyle', fontName='DejaVuSans', fontSize=7, alignment=1)),
        Paragraph("Остаток на<br/>конец<br/>периода", ParagraphStyle(name='HeaderStyle', fontName='DejaVuSans', fontSize=7, alignment=1)),
        Paragraph("Остаток<br/>на конец<br/>периода в днях", ParagraphStyle(name='HeaderStyle', fontName='DejaVuSans', fontSize=7, alignment=1)),
        Paragraph("Динамика<br/>неделя", ParagraphStyle(name='HeaderStyle', fontName='DejaVuSans', fontSize=7, alignment=1)),
        Paragraph("Динамика<br/>месяц", ParagraphStyle(name='HeaderStyle', fontName='DejaVuSans', fontSize=7, alignment=1)),
        Paragraph("Динамика<br/>год", ParagraphStyle(name='HeaderStyle', fontName='DejaVuSans', fontSize=7, alignment=1))
    ]
    table_data = [headers]

    # Функция создания строки таблицы
    def create_row(entry: Dict, label: str = None) -> list:
        return [
            f"{label}" if label else entry.get("label", ""),
            f"{safe_float(entry.get('remainder_end')):,.0f}".replace(',', ' '),
            f"{safe_float(entry.get('turnover_in_days')):.1f}",
            f"{safe_float(entry.get('turnover_in_days_dynamic_week')):.1f}",
            f"{safe_float(entry.get('turnover_in_days_dynamic_month')):.1f}",
            f"{safe_float(entry.get('turnover_in_days_dynamic_year')):.1f}",
        ]

    # Строки по точкам
    for item in data.get("data", []):
        table_data.append(create_row(item))

    # Итоговая строка "Всего"
    if sum_data := data.get("sum"):
        table_data.append(create_row(sum_data, label="Всего"))

    # Ширина колонок
    col_widths = [1.5 * inch] + [1 * inch] * (len(headers) - 1)

    # Создание таблицы
    table = Table(table_data, colWidths=col_widths)

    # Стилизация таблицы
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Центрирование всех ячеек
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Вертикальное центрирование
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -2 if sum_data else -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]

    if sum_data:
        table_style.append(('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey))

    # Добавляем раскраску для динамических колонок (3, 4, 5 - неделя, месяц, год)
    for row in range(1, len(table_data)):
        for col in [3, 4, 5]:  # Индексы динамических колонок
            value = safe_float(table_data[row][col])
            if value > 0:
                # Пастельно-красный
                table_style.append(('BACKGROUND', (col, row), (col, row), colors.HexColor("#FFCDD2")))
            elif value < 0:
                # Пастельно-зеленый
                table_style.append(('BACKGROUND', (col, row), (col, row), colors.HexColor("#C8E6C9")))

    table.setStyle(TableStyle(table_style))

    elements.append(table)
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer


def create_pdf_report_for_turnover_analysis(data: Union[Dict, List[Dict]]) -> BytesIO:
    """Создаёт PDF-отчёт по оборачиваемости (только показатели по ТЗ)."""

    if isinstance(data, list):
        data = data[0] if data else {}

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4))

    # Шрифт
    font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    elements = []
    title_style = ParagraphStyle(name='TitleStyle', fontName='DejaVuSans', fontSize=14, alignment=1)
    elements.append(Paragraph("Оборачиваемость остатков", title_style))
    elements.append(Spacer(1, 12))

    # Заголовки таблицы с выравниванием по центру
    headers = [
        Paragraph("Точка", ParagraphStyle(name='HeaderStyle', fontName='DejaVuSans', fontSize=7, alignment=1)),
        Paragraph("Остаток на<br/>конец<br/>периода", ParagraphStyle(name='HeaderStyle', fontName='DejaVuSans', fontSize=7, alignment=1)),
        Paragraph("Остаток<br/>на конец<br/>периода в днях", ParagraphStyle(name='HeaderStyle', fontName='DejaVuSans', fontSize=7, alignment=1)),
        Paragraph("Динамика<br/>неделя", ParagraphStyle(name='HeaderStyle', fontName='DejaVuSans', fontSize=7, alignment=1)),
        Paragraph("Динамика<br/>месяц", ParagraphStyle(name='HeaderStyle', fontName='DejaVuSans', fontSize=7, alignment=1)),
        Paragraph("Динамика<br/>год", ParagraphStyle(name='HeaderStyle', fontName='DejaVuSans', fontSize=7, alignment=1))
    ]
    table_data = [headers]

    # Функция для строки таблицы
    def create_row(entry: Dict, label: str = None) -> list:
        return [
            f"{label}" if label else entry.get("label", ""),
            f"{safe_float(entry.get('remainder_end')):,.0f}".replace(',', ' '),
            f"{safe_float(entry.get('turnover_in_days')):.1f}",
            f"{safe_float(entry.get('turnover_in_days_dynamic_week')):.1f}",
            f"{safe_float(entry.get('turnover_in_days_dynamic_month')):.1f}",
            f"{safe_float(entry.get('turnover_in_days_dynamic_year')):.1f}",
        ]

    # Добавление строк
    for item in data.get("data", []):
        table_data.append(create_row(item))

    # Итоговая строка "Всего"
    if sum_data := data.get("sum"):
        table_data.append(create_row(sum_data, label="Всего"))

    # Ширина колонок
    col_widths = [2.5 * inch] + [1 * inch] * (len(headers) - 1)

    # Создание таблицы
    table = Table(table_data, colWidths=col_widths)

    # Стили
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Центрирование всех ячеек
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Вертикальное центрирование
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -2 if sum_data else -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]

    if sum_data:
        table_style.append(('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey))

    # Добавляем раскраску для динамических колонок (3, 4, 5 - неделя, месяц, год)
    for row in range(1, len(table_data)):
        for col in [3, 4, 5]:  # Индексы динамических колонок
            value = safe_float(table_data[row][col])
            if value > 0:
                # Пастельно-красный
                table_style.append(('BACKGROUND', (col, row), (col, row), colors.HexColor("#FFCDD2")))
            elif value < 0:
                # Пастельно-зеленый
                table_style.append(('BACKGROUND', (col, row), (col, row), colors.HexColor("#C8E6C9")))

    table.setStyle(TableStyle(table_style))
    elements.append(table)

    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer
