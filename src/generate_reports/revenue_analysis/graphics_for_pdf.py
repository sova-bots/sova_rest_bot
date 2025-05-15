import logging
import json
from io import BytesIO
from aiogram import F, Router
from aiogram.types import CallbackQuery, BufferedInputFile
from fpdf import FPDF
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import os
from typing import Dict, List

analys_revenue_pdf_router = Router()


def format_currency(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " ₽"


def format_percentage(value: int) -> str:
    return f"{value}%"


def create_dynamics_graph(data: Dict) -> BytesIO:
    fig = plt.figure(figsize=(8, 4))

    periods = ['Неделя', 'Месяц', 'Год']
    values = [
        data['sum']['revenue_dynamics_week'],
        data['sum']['revenue_dynamics_month'],
        data['sum']['revenue_dynamics_year']
    ]
    colors = ['#FFD700' if x >= 0 else '#FF6347' for x in values]
    bars = plt.bar(periods, values, color=colors)

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2., height,
                 f'{height}%', ha='center', va='bottom', fontsize=10)

    plt.title('Динамика выручки (ИТОГ)', fontsize=12)
    plt.ylabel('Изменение (%)', fontsize=10)
    plt.tick_params(axis='both', which='major', labelsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    img_bytes = BytesIO()
    plt.savefig(img_bytes, format='png', bbox_inches='tight', dpi=150)
    plt.close()
    img_bytes.seek(0)

    return img_bytes


def create_pdf_report(data: Dict) -> BytesIO:
    pdf = FPDF(orientation='L')
    pdf.add_page()

    try:
        font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSans.ttf')
        pdf.add_font('DejaVu', '', font_path, uni=True)
        pdf.add_font('DejaVu', 'B', font_path, uni=True)
        font_name = 'DejaVu'
    except Exception as e:
        logging.warning(f"DejaVuSans не найден, используем Arial: {e}")
        pdf.set_font("Arial", '', 12)
        font_name = 'Arial'

    # Цвета для динамики
    POSITIVE_COLOR = (197, 226, 132)  # Зеленый
    NEGATIVE_COLOR = (211, 154, 128)  # Красный
    HEADER_COLOR = (220, 220, 220)  # Серый для заголовков

    pdf.set_font(font_name, 'B', 16)
    pdf.cell(0, 10, txt="ОТЧЁТ ПО ВЫРУЧКЕ", ln=True, align='C')

    pdf.set_font(font_name, '', 12)
    pdf.cell(0, 8, txt=f"Текущая выручка: {format_currency(data['sum']['revenue'])}", ln=True)
    pdf.cell(0, 8, txt=f"Прогноз: {format_currency(data['sum']['revenue_forecast'])}", ln=True)
    pdf.ln(8)

    graph_bytes = create_dynamics_graph(data)
    graph_path = 'temp_dynamics.png'
    with open(graph_path, 'wb') as f:
        f.write(graph_bytes.getvalue())

    pdf.image(graph_path, x=10, y=pdf.get_y(), w=120)
    pdf.ln(65)

    pdf.set_font(font_name, 'B', 12)
    pdf.cell(0, 8, txt="Сравнительный анализ", ln=True, align='C')

    col_widths = [90, 45, 35, 35, 35, 45]
    headers = ["Магазин", "Выручка", "Неделя", "Месяц", "Год", "Прогноз"]

    # Заголовки таблицы
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1, align='C', fill=True)
    pdf.ln()

    # Данные таблицы
    pdf.set_font(font_name, '', 10)
    for store in data['data']:
        label = store['label'].replace("Рогалик", "").strip()
        if len(label) > 40:
            label = label[:37] + "..."

        # Название магазина (без заливки)
        pdf.set_fill_color(255, 255, 255)  # Белый фон
        pdf.cell(col_widths[0], 8, label, border=1, align='C')

        # Выручка (без заливки)
        pdf.cell(col_widths[1], 8, format_currency(store['revenue']), border=1, align='C')

        # Динамика за неделю
        week_dynamics = store['revenue_dynamics_week']
        fill_color = POSITIVE_COLOR if week_dynamics >= 0 else NEGATIVE_COLOR
        pdf.set_fill_color(*fill_color)
        pdf.cell(col_widths[2], 8, format_percentage(week_dynamics), border=1, align='C', fill=True)

        # Динамика за месяц
        month_dynamics = store['revenue_dynamics_month']
        fill_color = POSITIVE_COLOR if month_dynamics >= 0 else NEGATIVE_COLOR
        pdf.set_fill_color(*fill_color)
        pdf.cell(col_widths[3], 8, format_percentage(month_dynamics), border=1, align='C', fill=True)

        # Динамика за год
        year_dynamics = store['revenue_dynamics_year']
        fill_color = POSITIVE_COLOR if year_dynamics >= 0 else NEGATIVE_COLOR
        pdf.set_fill_color(*fill_color)
        pdf.cell(col_widths[4], 8, format_percentage(year_dynamics), border=1, align='C', fill=True)

        # Прогноз (без заливки)
        pdf.set_fill_color(255, 255, 255)
        pdf.cell(col_widths[5], 8, format_currency(store['revenue_forecast']), border=1, align='C')

        pdf.ln()

    # Итоговая строка
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    pdf.cell(col_widths[0], 8, data['sum']['label'], border=1, align='C', fill=True)
    pdf.cell(col_widths[1], 8, format_currency(data['sum']['revenue']), border=1, align='C', fill=True)

    # Динамика за неделю (итог)
    week_total = data['sum']['revenue_dynamics_week']
    fill_color = POSITIVE_COLOR if week_total >= 0 else NEGATIVE_COLOR
    pdf.set_fill_color(*fill_color)
    pdf.cell(col_widths[2], 8, format_percentage(week_total), border=1, align='C', fill=True)

    # Динамика за месяц (итог)
    month_total = data['sum']['revenue_dynamics_month']
    fill_color = POSITIVE_COLOR if month_total >= 0 else NEGATIVE_COLOR
    pdf.set_fill_color(*fill_color)
    pdf.cell(col_widths[3], 8, format_percentage(month_total), border=1, align='C', fill=True)

    # Динамика за год (итог)
    year_total = data['sum']['revenue_dynamics_year']
    fill_color = POSITIVE_COLOR if year_total >= 0 else NEGATIVE_COLOR
    pdf.set_fill_color(*fill_color)
    pdf.cell(col_widths[4], 8, format_percentage(year_total), border=1, align='C', fill=True)

    # Прогноз (итог)
    pdf.set_fill_color(*HEADER_COLOR)
    pdf.cell(col_widths[5], 8, format_currency(data['sum']['revenue_forecast']), border=1, align='C', fill=True)

    pdf.ln()

    pdf_output = BytesIO()
    pdf_output.write(pdf.output(dest='S').encode('latin1'))
    pdf_output.seek(0)

    if os.path.exists(graph_path):
        os.remove(graph_path)

    return pdf_output


def load_revenue_data(filepath: str) -> Dict:
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if isinstance(data, list) and len(data) > 0:
                return data[0]  # Берем первый словарь из списка
            elif isinstance(data, dict):
                return data
            else:
                logging.error("Некорректный формат JSON: не словарь и не список словарей.")
                return {}
    except Exception as e:
        logging.error(f"Ошибка при чтении файла {filepath}: {e}")
        return {}



@analys_revenue_pdf_router.callback_query(F.data == "revenue_analysis_pdf")
async def handle_format_pdf(callback_query: CallbackQuery):
    await callback_query.answer("Формирую PDF отчёт...")

    filepath = r"revenue_analys.json"
    revenue_data = load_revenue_data(filepath)

    if not revenue_data:
        await callback_query.message.answer("Ошибка при загрузке данных для отчёта.")
        return

    try:
        pdf_buffer = create_pdf_report(revenue_data)
    except Exception as e:
        logging.error(f"Ошибка при создании PDF: {e}")
        await callback_query.message.answer("Ошибка при создании PDF-отчёта.")
        return

    try:
        input_file = BufferedInputFile(pdf_buffer.getvalue(), filename="revenue_analysis.pdf")
        await callback_query.message.answer_document(input_file, caption="Ваш отчёт по анализу выручки:")
    except Exception as e:
        logging.error(f"Ошибка при отправке PDF: {e}")
        await callback_query.message.answer("Ошибка при отправке отчёта.")


def main_generate_revenue_pdf(filepath: str) -> BytesIO | None:
    revenue_data = load_revenue_data(filepath)
    if not revenue_data:
        print("Ошибка при загрузке данных для отчёта.")
        return None

    try:
        pdf_buffer = create_pdf_report(revenue_data)
        print("PDF успешно создан: revenue_analysis.pdf")
        return pdf_buffer
    except Exception as e:
        logging.error(f"Ошибка при создании PDF: {e}")
        print("Ошибка при создании PDF-отчёта.")
        return None


if __name__ == "__main__":
    filepath = r"revenue_analys.json"
    pdf_bytes = main_generate_revenue_pdf(filepath)
    if pdf_bytes:
        with open("revenue_analysis.pdf", "wb") as f:
            f.write(pdf_bytes.getvalue())
        print("PDF отчёт сохранён!")
