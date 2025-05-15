import os
from typing import Union, Dict, List
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


def safe_float(value):
    try:
        return float(value) if value is not None else 0.0
    except (ValueError, TypeError):
        return 0.0


def apply_dynamics_coloring(table_data: List[List[str]], columns: List[int], start_row: int = 1) -> List[tuple]:
    """
    Возвращает список стилей для покраски ячеек с динамикой в таблице.
    :param table_data: Данные таблицы (включая заголовки).
    :param columns: Индексы колонок, где нужно проверять значения.
    :param start_row: С какой строки начинать обработку (0 — с заголовка, 1 — с данных).
    """
    pastel_red = colors.HexColor("#F4CCCC")
    pastel_green = colors.HexColor("#D9EAD3")
    styles = []

    for row_index, row in enumerate(table_data[start_row:], start=start_row):
        for col_index in columns:
            try:
                value_str = row[col_index].replace('%', '').replace(',', '.')
                value = float(value_str)
                if value > 0:
                    styles.append(('BACKGROUND', (col_index, row_index), (col_index, row_index), pastel_red))
                elif value < 0:
                    styles.append(('BACKGROUND', (col_index, row_index), (col_index, row_index), pastel_green))
            except:
                continue
    return styles


def create_pdf_report_for_food_cost(data: Union[Dict, List[Dict]]) -> BytesIO:
    """Создаёт PDF-отчёт по фудкосту."""

    if isinstance(data, list):
        data = data[0] if data else {}

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4))

    # Шрифт
    font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    # Заголовок
    elements = []
    title_style = ParagraphStyle(name='TitleStyle', fontName='DejaVuSans', fontSize=14, alignment=1)
    elements.append(Paragraph("Фудкост", title_style))
    elements.append(Spacer(1, 12))

    # Заголовки таблицы
    headers = [
        "Точка",
        "Фудкост", "Динамика \nнеделя", "Динамика \nмесяц", "Динамика \nгод",
        "Фудкост \nБар", "Динамика \nнеделя \nБар", "Динамика \nмесяц \nБар", "Динамика \nгод \nБар",
        "Фудкост \nКухня", "Динамика \nнеделя \nКухня", "Динамика \nмесяц \nКухня", "Динамика \nгод \nКухня"
    ]
    table_data = [headers]

    # Список индексов колонок с динамикой
    dynamic_columns = [2, 3, 4, 6, 7, 8, 10, 11, 12]

    # Добавление строк
    def create_row(source: Dict, label: str = None) -> List:
        return [
            f"{label}" if label else source.get("label", ""),
            f"{safe_float(source.get('food_cost')):.1f}%",
            f"{safe_float(source.get('food_cost_dynamics_week')):.1f}%",
            f"{safe_float(source.get('food_cost_dynamics_month')):.1f}%",
            f"{safe_float(source.get('food_cost_dynamics_year')):.1f}%",
            f"{safe_float(source.get('food_cost_bar')):.1f}%",
            f"{safe_float(source.get('food_cost_bar_dynamics_week')):.1f}%",
            f"{safe_float(source.get('food_cost_bar_dynamics_month')):.1f}%",
            f"{safe_float(source.get('food_cost_bar_dynamics_year')):.1f}%",
            f"{safe_float(source.get('food_cost_kitchen')):.1f}%",
            f"{safe_float(source.get('food_cost_kitchen_dynamics_week')):.1f}%",
            f"{safe_float(source.get('food_cost_kitchen_dynamics_month')):.1f}%",
            f"{safe_float(source.get('food_cost_kitchen_dynamics_year')):.1f}%",
        ]

    for item in data.get("data", []):
        table_data.append(create_row(item))

    if sum_data := data.get("sum"):
        table_data.append(create_row(sum_data, label="Всего"))

    # Ширина колонок
    col_widths = [1.9 * inch] + [0.8 * inch] * (len(headers) - 1)

    # Таблица
    table = Table(table_data, colWidths=col_widths)

    # Стили таблицы
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -2 if sum_data else -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]

    if sum_data:
        table_style.append(('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey))

    # Окрашивание ячеек с динамикой
    for row_index, row in enumerate(table_data[1:], start=1):  # начиная со второй строки
        for col_index in dynamic_columns:
            try:
                value_str = row[col_index].replace('%', '').replace(',', '.')
                value = float(value_str)
                if value > 0:
                    bg_color = colors.HexColor("#F4CCCC")
                elif value < 0:
                    bg_color = colors.HexColor("#D9EAD3")
                else:
                    continue  # не красим
                table_style.append(('BACKGROUND', (col_index, row_index), (col_index, row_index), bg_color))
            except Exception:
                continue  #

    table.setStyle(TableStyle(table_style))

    elements.append(table)
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer


def create_pdf_report_for_food_cost_analysis(data: Union[Dict, List[Dict]]) -> BytesIO:
    if isinstance(data, list):
        data = data[0] if data else {}

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4))

    font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    elements = []
    title_style = ParagraphStyle(name='TitleStyle', fontName='DejaVuSans', fontSize=14, alignment=1)
    subtitle_style = ParagraphStyle(name='TitleStyle', fontName='DejaVuSans', fontSize=11, alignment=1)
    elements.append(Paragraph("Фудкост", title_style))
    elements.append(Spacer(1, 12))

    # ---------- Таблица 1 ----------
    headers_items = ["Товар", "Фудкост", "Динамика неделя", "Динамика месяц", "Динамика год"]
    table_items = [headers_items]

    for item in data.get("data", []):
        table_items.append([
            item.get("label", ""),
            f"{safe_float(item.get('food_cost')):.1f}%",
            f"{safe_float(item.get('food_cost_dynamics_week')):.1f}%",
            f"{safe_float(item.get('food_cost_dynamics_month')):.1f}%",
            f"{safe_float(item.get('food_cost_dynamics_year')):.1f}%",
        ])

    col_widths_items = [2.5 * inch] + [1 * inch] * (len(headers_items) - 1)
    table1 = Table(table_items, colWidths=col_widths_items)

    table1_base_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]
    # Покраска динамики (неделя, месяц, год)
    table1_style = table1_base_style + apply_dynamics_coloring(table_items, columns=[2, 3, 4])
    table1.setStyle(TableStyle(table1_style))

    elements.append(Paragraph("1. Фудкост", subtitle_style))
    elements.append(Spacer(1, 8))
    elements.append(table1)
    elements.append(Spacer(1, 16))

    # ---------- Таблица 2 ----------
    headers_sum = [
        " ",
        "Фудкост", "Динамика \nнеделя", "Динамика \nмесяц", "Динамика \nгод",
        "Фудкост \nБар", "Динамика \nнеделя \nБар", "Динамика \nмесяц \nБар", "Динамика \nгод \nБар",
        "Фудкост \nКухня", "Динамика \nнеделя \nКухня", "Динамика \nмесяц \nКухня", "Динамика \nгод \nКухня"
    ]
    table_sum = [headers_sum]

    sum_data = data.get("sum", {})
    row_sum = [
        str(sum_data.get("label", "Итого")),
        f"{safe_float(sum_data.get('food_cost')):.1f}%",
        f"{safe_float(sum_data.get('food_cost_dynamics_week')):.1f}%",
        f"{safe_float(sum_data.get('food_cost_dynamics_month')):.1f}%",
        f"{safe_float(sum_data.get('food_cost_dynamics_year')):.1f}%",
        f"{safe_float(sum_data.get('food_cost_bar')):.1f}%",
        f"{safe_float(sum_data.get('food_cost_bar_dynamics_week')):.1f}%",
        f"{safe_float(sum_data.get('food_cost_bar_dynamics_month')):.1f}%",
        f"{safe_float(sum_data.get('food_cost_bar_dynamics_year')):.1f}%",
        f"{safe_float(sum_data.get('food_cost_kitchen')):.1f}%",
        f"{safe_float(sum_data.get('food_cost_kitchen_dynamics_week')):.1f}%",
        f"{safe_float(sum_data.get('food_cost_kitchen_dynamics_month')):.1f}%",
        f"{safe_float(sum_data.get('food_cost_kitchen_dynamics_year')):.1f}%",
    ]
    table_sum.append(row_sum)

    col_widths_sum = [1.2 * inch] + [0.7 * inch] * (len(headers_sum) - 1)
    table2 = Table(table_sum, colWidths=col_widths_sum)

    table2_base_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
    ]
    # Покраска динамики (все поля динамики)
    table2_style = table2_base_style + apply_dynamics_coloring(table_sum, columns=[2, 3, 4, 6, 7, 8, 10, 11, 12])
    table2.setStyle(TableStyle(table2_style))

    elements.append(Paragraph("2. Итоговые показатели (Всего)", subtitle_style))
    elements.append(Spacer(1, 8))
    elements.append(table2)

    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer
