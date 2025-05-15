from typing import Dict, Union, List
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def safe_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def format_percent(val):
    try:
        return f"{float(val):.1f}%"  # Убрано abs() для сохранения знака
    except (TypeError, ValueError):
        return "-"


def style_by_value(row_idx, col_idx, value):
    try:
        num = float(value)
        if num > 0:
            return ('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), colors.HexColor('#d0f0c0'))
        elif num < 0:
            return ('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), colors.HexColor('#f4cccc'))
    except:
        pass
    return None


def create_pdf_report_for_markup(data: Union[Dict, list]) -> BytesIO:
    if isinstance(data, list):
        data = data[0] if data else {}

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4))

    font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    elements = []
    title_style = ParagraphStyle(name='TitleStyle', fontName='DejaVuSans', fontSize=14, alignment=1)
    elements.append(Paragraph("Наценка", title_style))
    elements.append(Spacer(1, 12))

    headers = ["Точка", "Наценка", "Динамика \nнеделя", "Динамика \nмесяц", "Динамика \nгод"]
    table_data = [headers]
    cell_styles = []

    def create_row(entry: Dict, label: str = None, row_idx: int = 1) -> list:
        row = [
            f"{label}" if label else entry.get("label", ""),
            format_percent(entry.get('markup')),
            format_percent(entry.get('markup_dynamics_week')),
            format_percent(entry.get('markup_dynamics_month')),
            format_percent(entry.get('markup_dynamics_year')),
        ]
        for i, key in enumerate(['markup_dynamics_week', 'markup_dynamics_month', 'markup_dynamics_year']):
            style = style_by_value(row_idx, i + 2, entry.get(key))
            if style:
                cell_styles.append(style)
        return row

    for idx, item in enumerate(data.get("data", []), start=1):
        table_data.append(create_row(item, row_idx=idx))

    # if sum_data := data.get("sum"):
    #     table_data.append(create_row(sum_data, label="Всего", row_idx=len(table_data)))

    sum_data = None

    col_widths = [2.5 * inch] + [1.5 * inch] * (len(headers) - 1)
    table = Table(table_data, colWidths=col_widths)

    base_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -2 if sum_data else -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]
    if sum_data:
        base_style.append(('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey))

    table.setStyle(TableStyle(base_style + cell_styles))
    elements.append(table)
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer


def safe_value(value):
    try:
        return f"{int(value)}"
    except (ValueError, TypeError):
        return "-"


def safe_delta(value):
    try:
        val = int(value)
        return f"{val:+d}"
    except (ValueError, TypeError):
        return "-"

def create_pdf_report_for_markup_analysis(data: Union[Dict, List[Dict]]) -> BytesIO:
    if isinstance(data, list):
        data = data[0] if data else {}

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=30, bottomMargin=30)

    font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    elements = []
    title_style = ParagraphStyle(name='Title', fontName='DejaVuSans', fontSize=14, alignment=1)
    elements.append(Paragraph("Наценка", title_style))
    elements.append(Spacer(1, 12))

    headers = ["Товар", "Наценка", "Динамика \nнеделя", "Динамика \nмесяц", "Динамика \nгод"]
    table_data = [headers]
    cell_styles = []


    def create_row(entry: Dict, label_override: str = None, row_idx: int = 1) -> list:
        row = [
            f"{label_override}" if label_override else entry.get("label", ""),
            format_percent(entry.get("markup")),
            format_percent(entry.get("markup_dynamics_week")),
            format_percent(entry.get("markup_dynamics_month")),
            format_percent(entry.get("markup_dynamics_year")),
        ]
        for i, key in enumerate(['markup_dynamics_week', 'markup_dynamics_month', 'markup_dynamics_year']):
            style = style_by_value(row_idx, i + 2, entry.get(key))
            if style:
                cell_styles.append(style)
        return row

    for idx, item in enumerate(data.get("data", []), start=1):
        table_data.append(create_row(item, row_idx=idx))

    # if sum_data := data.get("sum"):
    #     table_data.append(create_row(sum_data, label_override="Всего", row_idx=len(table_data)))

    sum_data = None  # Удаляем строку с итогами

    col_widths = [3.0 * inch] + [1.5 * inch] * (len(headers) - 1)
    table = Table(table_data, colWidths=col_widths)

    base_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4BACC6")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
    ]
    if sum_data:
        base_style.append(('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey))

    table.setStyle(TableStyle(base_style + cell_styles))
    elements.append(table)
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer
