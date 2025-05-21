import json
import os
import logging
import tempfile

from fpdf import FPDF
import matplotlib.pyplot as plt
from io import BytesIO
from typing import Dict, Union, List

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('report_generator.log'),
        logging.StreamHandler()
    ]
)

POSITIVE_COLOR = (197, 226, 132)
NEGATIVE_COLOR = (211, 154, 128)
HEADER_COLOR = (220, 220, 220)


class PDFWithFooter(FPDF):
    def footer(self):
        self.set_y(-15)  # Отступ от нижнего края страницы
        self.set_font("DejaVu", "I", 10)
        page_text = f"Страница {self.page_no()}"
        self.cell(0, 10, page_text, align='C')


def format_currency(value):
    try:
        if value is None:
            return "—"
        if isinstance(value, str):
            value = value.lstrip("0") or "0"
            value = int(value)
        elif not isinstance(value, int):
            value = int(value)
        return f"{value:,}".replace(",", " ")
    except Exception as e:
        logging.error(f"Ошибка форматирования валюты: {e}")
        return str(value)


def format_percentage(value: Union[int, float, None]) -> str:
    try:
        if value is None:
            return "—"
        return f"{value}%"
    except Exception as e:
        logging.error(f"Ошибка форматирования процентов: {e}")
        return str(value) + "%"


def format_number(value: Union[int, float, None]) -> str:
    try:
        if value is None:
            return "—"
        return str(value)
    except Exception as e:
        logging.error(f"Ошибка форматирования числа: {e}")
        return str(value)


def initialize_pdf_with_font(pdf_class=FPDF, orientation='L'):
    pdf = pdf_class(orientation=orientation)

    try:
        # Попробуем найти шрифт в разных местах
        possible_font_paths = [
            os.path.join(os.path.dirname(__file__), 'DejaVuSans.ttf'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'DejaVuSans.ttf'),
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            'DejaVuSans.ttf'
        ]

        font_path = None
        for path in possible_font_paths:
            if os.path.exists(path):
                font_path = path
                break

        if not font_path:
            raise FileNotFoundError("Файл шрифта DejaVuSans.ttf не найден")

        pdf.add_font('DejaVu', '', font_path, uni=True)
        pdf.add_font('DejaVu', 'B', font_path, uni=True)
        pdf.add_font('DejaVu', 'I', font_path, uni=True)
        font_name = 'DejaVu'
    except Exception as e:
        logging.warning(f"Не удалось загрузить DejaVuSans.ttf, используем стандартные шрифты: {e}")
        try:
            # Попробуем использовать Arial
            pdf.add_font('Arial', '', 'arial.ttf', uni=True)
            pdf.add_font('Arial', 'B', 'arialbd.ttf', uni=True)
            pdf.add_font('Arial', 'I', 'ariali.ttf', uni=True)
            font_name = 'Arial'
        except:
            # В крайнем случае используем встроенные шрифты (не поддерживают кириллицу)
            font_name = 'helvetica'

    return pdf, font_name


def revenue_parameters_create_pdf_report(data: List[Dict]) -> BytesIO:
    pdf, font_name = initialize_pdf_with_font(PDFWithFooter, 'L')
    pdf.add_page()

    pdf.set_font(font_name, 'B', 16)
    pdf.cell(0, 10, txt="Отчёт по выручке", ln=True, align='C')

    pdf.set_font(font_name, '', 12)
    sum_data = data[0].get('sum', {})
    pdf.cell(0, 8, txt=f"Текущая выручка: {format_currency(sum_data.get('revenue', 0))}", ln=True)
    pdf.cell(0, 8, txt=f"Прогноз: {format_currency(sum_data.get('revenue_forecast', 0))}", ln=True)
    pdf.ln(8)

    col_widths = [90, 45, 35, 35, 35, 45]
    headers = ["Магазин", "Выручка", "Выручка неделя", "Выручка месяц", "Выручка год", "Прогноз"]
    key_to_header = {
        'revenue_dynamics_week': "Выручка неделя",
        'revenue_dynamics_month': "Выручка месяц",
        'revenue_dynamics_year': "Выручка год"
    }

    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1, align='C', fill=True)
    pdf.ln()

    pdf.set_font(font_name, '', 10)
    for store in data[0].get('data', []):
        label = store['label'].replace("Рогалик", "").strip()
        label = (label[:37] + "...") if len(label) > 40 else label
        pdf.cell(col_widths[0], 8, label, border=1, align='C')
        pdf.cell(col_widths[1], 8, format_currency(store.get('revenue', 0)), border=1, align='C')

        for key in ['revenue_dynamics_week', 'revenue_dynamics_month', 'revenue_dynamics_year']:
            val = store.get(key, 0)
            col_index = headers.index(key_to_header[key])
            pdf.cell(col_widths[col_index], 8, format_currency(val), border=1, align='C')

        pdf.cell(col_widths[5], 8, format_currency(store.get('revenue_forecast', 0)), border=1, align='C')
        pdf.ln()

    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    pdf.cell(col_widths[0], 8, sum_data.get('label', 'Итого'), border=1, align='C', fill=True)
    pdf.cell(col_widths[1], 8, format_currency(sum_data.get('revenue', 0)), border=1, align='C', fill=True)

    for key in ['revenue_dynamics_week', 'revenue_dynamics_month', 'revenue_dynamics_year']:
        val = sum_data.get(key, 0)
        col_index = headers.index(key_to_header[key])
        pdf.cell(col_widths[col_index], 8, format_currency(val), border=1, align='C', fill=True)

    pdf.cell(col_widths[5], 8, format_currency(sum_data.get('revenue_forecast', 0)), border=1, align='C', fill=True)
    pdf.ln()

    pdf_output = BytesIO()
    pdf_output.write(bytes(pdf.output(dest='S').encode('latin1')))
    pdf_output.seek(0)
    return pdf_output


def load_revenue_data(filepath: str) -> Union[Dict, List[Dict]]:
    """Загружает данные о выручке из JSON файла."""
    logging.info(f"Попытка загрузки данных из {filepath}")
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Файл не найден: {filepath}")

        file_size = os.path.getsize(filepath)
        logging.debug(f"Размер файла: {file_size} байт")
        if file_size == 0:
            raise ValueError("Файл пустой")

        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            if not content.strip():
                raise ValueError("Файл не содержит данных")

            logging.debug(f"Первые 100 символов файла: {content[:100]}...")
            data = json.loads(content)

            if not isinstance(data, (list, dict)):
                raise TypeError("Неподдерживаемый формат данных. Ожидается список или словарь.")

            logging.info(f"Успешно загружено {len(data) if isinstance(data, list) else '1'} записей")
            return data

    except json.JSONDecodeError as e:
        logging.error(f"Ошибка декодирования JSON: {e}")
        raise
    except Exception as e:
        logging.error(f"Ошибка загрузки данных: {e}", exc_info=True)
        raise


def revenue_parameters_create_pdf_report_analysis(data: List[Dict]) -> BytesIO:
    pdf, font_name = initialize_pdf_with_font(orientation='L')
    pdf.add_page()

    HEADER_COLOR = (220, 220, 220)  # Серый для заголовков
    DEFAULT_COLOR = (255, 255, 255)  # Белый по умолчанию

    # Обработка данных
    sum_data = data[0].get('sum', {})
    pdf.set_font(font_name, 'B', 16)
    pdf.cell(0, 10, txt="Гости/Чеки", ln=True, align='C')

    pdf.ln(10)

    col_widths = [90, 45, 35, 35, 35, 45]
    headers = ["Подразделение", "Гости", "Выручка неделя", "Выручка месяц", "Выручка год", "Чеки"]

    # Заголовки таблицы
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1, align='C', fill=True)
    pdf.ln()

    # Данные таблицы
    pdf.set_font(font_name, '', 10)
    for store in data[0].get('data', []):
        label = store['label']
        if len(label) > 40:
            label = label[:37] + "..."

        # Название подразделения
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[0], 8, label, border=1, align='C')

        # Посетители
        pdf.cell(col_widths[1], 8, format_currency(store.get('guests', 0)), border=1, align='C')

        # Выручка за неделю
        week_revenue = store.get('guests_dynamics_week', 0) or 0
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[2], 8, format_currency(week_revenue), border=1, align='C', fill=True)

        # Выручка за месяц
        month_revenue = store.get('guests_dynamics_month', 0) or 0
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[3], 8, format_currency(month_revenue), border=1, align='C', fill=True)

        # Выручка за год
        year_revenue = store.get('guests_dynamics_year', 0) or 0
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[4], 8, format_currency(year_revenue), border=1, align='C', fill=True)

        # Чеки
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[5], 8, format_currency(store.get('checks', 0)), border=1, align='C')

        pdf.ln()

    # Итоговая строка
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    pdf.cell(col_widths[0], 8, sum_data.get('label', 'Итого'), border=1, align='C', fill=True)
    pdf.cell(col_widths[1], 8, format_currency(sum_data.get('guests', 0)), border=1, align='C', fill=True)

    # Выручка за неделю (итог)
    week_total = sum_data.get('guests_dynamics_week', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[2], 8, format_currency(week_total), border=1, align='C', fill=True)

    # Выручка за месяц (итог)
    month_total = sum_data.get('guests_dynamics_month', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[3], 8, format_currency(month_total), border=1, align='C', fill=True)

    # Выручка за год (итог)
    year_total = sum_data.get('guests_dynamics_year', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[4], 8, format_currency(year_total), border=1, align='C', fill=True)

    # Чеки (итог)
    pdf.set_fill_color(*HEADER_COLOR)
    pdf.cell(col_widths[5], 8, format_currency(sum_data.get('checks', 0)), border=1, align='C', fill=True)

    pdf.ln(10)

    pdf.add_page()
    pdf.set_font(font_name, 'B', 16)
    pdf.cell(0, 10, txt="Средний чек", ln=True, align='C')
    pdf.ln(5)

    check_sum_data = data[0].get('sum', {})

    col_widths = [100, 40, 34, 34, 34]
    headers = ["Подразделение", "Средний чек", "Выручка неделя", "Выручка месяц", "Выручка год"]

    # Заголовки таблицы
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1, align='C', fill=True)
    pdf.ln()

    # Данные таблицы
    pdf.set_font(font_name, '', 10)
    for store in data[0].get('data', []):
        label = store.get('label', '')
        if len(label) > 60:
            label = label[:57] + "..."

        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[0], 8, label, border=1, align='C')

        # Средний чек
        pdf.cell(col_widths[1], 8, format_currency(store.get('avg_check', 0)), border=1, align='C')

        # Выручка за неделю
        week_revenue = store.get('avg_check_dynamics_week', 0) or 0
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[2], 8, format_currency(week_revenue), border=1, align='C', fill=True)

        # Выручка за месяц
        month_revenue = store.get('avg_check_dynamics_month', 0) or 0
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[3], 8, format_currency(month_revenue), border=1, align='C', fill=True)

        # Выручка за год
        year_revenue = store.get('avg_check_dynamics_year', 0) or 0
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[4], 8, format_currency(year_revenue), border=1, align='C', fill=True)

        pdf.ln()

    # Итоговая строка
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    pdf.cell(col_widths[0], 8, check_sum_data.get('label', 'Итого'), border=1, align='C', fill=True)
    pdf.cell(col_widths[1], 8, format_currency(check_sum_data.get('avg_check', 0)), border=1, align='C', fill=True)

    week_total = check_sum_data.get('avg_check_dynamics_week', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[2], 8, format_currency(week_total), border=1, align='C', fill=True)

    month_total = check_sum_data.get('avg_check_dynamics_month', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[3], 8, format_currency(month_total), border=1, align='C', fill=True)

    year_total = check_sum_data.get('avg_check_dynamics_year', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[4], 8, format_currency(year_total), border=1, align='C', fill=True)

    # --- Новая страница: Анализ выручки ---
    pdf.add_page()
    pdf.set_font(font_name, 'B', 16)
    pdf.cell(0, 10, txt="Выручка", ln=True, align='C')
    pdf.ln(5)

    revenue_sum_data = data[0].get('sum', {})

    col_widths = [100, 40, 34, 34, 34]
    headers = ["Подразделение", "Выручка", "Выручка неделя", "Выручка месяц", "Выручка год"]

    # Заголовки таблицы
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1, align='C', fill=True)
    pdf.ln()

    # Данные таблицы
    pdf.set_font(font_name, '', 10)
    for store in data[0].get('data', []):
        label = store.get('label', '')
        if len(label) > 60:
            label = label[:57] + "..."

        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[0], 8, label, border=1, align='C')

        # Выручка
        pdf.cell(col_widths[1], 8, format_currency(store.get('revenue', 0)), border=1, align='C')

        # Выручка за неделю
        week_revenue = store.get('revenue_dynamics_week', 0) or 0
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[2], 8, format_currency(week_revenue), border=1, align='C', fill=True)

        # Выручка за месяц
        month_revenue = store.get('revenue_dynamics_month', 0) or 0
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[3], 8, format_currency(month_revenue), border=1, align='C', fill=True)

        # Выручка за год
        year_revenue = store.get('revenue_dynamics_year', 0) or 0
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[4], 8, format_currency(year_revenue), border=1, align='C', fill=True)

        pdf.ln()

    # Итоговая строка
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    pdf.cell(col_widths[0], 8, revenue_sum_data.get('label', 'Итого'), border=1, align='C', fill=True)
    pdf.cell(col_widths[1], 8, format_currency(revenue_sum_data.get('revenue', 0)), border=1, align='C', fill=True)

    week_total = revenue_sum_data.get('revenue_dynamics_week', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[2], 8, format_currency(week_total), border=1, align='C', fill=True)

    month_total = revenue_sum_data.get('revenue_dynamics_month', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[3], 8, format_currency(month_total), border=1, align='C', fill=True)

    year_total = revenue_sum_data.get('revenue_dynamics_year', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[4], 8, format_currency(year_total), border=1, align='C', fill=True)

    pdf.add_page()
    pdf.set_font(font_name, 'B', 16)
    pdf.cell(0, 10, txt="Выручка по направлениям", ln=True, align='C')
    pdf.ln(5)

    direction_sum_data = data[0].get('sum', {})

    pdf.set_font(font_name, 'B', 12)
    pdf.cell(0, 8, txt="Сравнительный анализ по направлениям", ln=True, align='C')

    col_widths = [100, 40, 34, 34, 34]
    headers = ["Направление", "Выручка", "Выручка неделя", "Выручка месяц", "Выручка год"]

    # Заголовки таблицы
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1, align='C', fill=True)
    pdf.ln()

    # Данные таблицы
    pdf.set_font(font_name, '', 10)
    for direction in data[0].get('data', []):
        label = direction.get('label', '')
        if len(label) > 60:
            label = label[:57] + "..."

        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[0], 8, label, border=1, align='C')

        # Выручка
        pdf.cell(col_widths[1], 8, format_currency(direction.get('revenue', 0)), border=1, align='C')

        # Выручка за неделю
        week_revenue = direction.get('revenue_dynamics_week', 0)
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[2], 8, format_currency(week_revenue), border=1, align='C', fill=True)

        # Выручка за месяц
        month_revenue = direction.get('revenue_dynamics_month', 0)
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[3], 8, format_currency(month_revenue), border=1, align='C', fill=True)

        # Выручка за год
        year_revenue = direction.get('revenue_dynamics_year', 0)
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[4], 8, format_currency(year_revenue), border=1, align='C', fill=True)

        pdf.ln()

    # Итоговая строка
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    pdf.cell(col_widths[0], 8, direction_sum_data.get('label', 'Итого'), border=1, align='C', fill=True)
    pdf.cell(col_widths[1], 8, format_currency(direction_sum_data.get('revenue', 0)), border=1, align='C', fill=True)

    week_total = direction_sum_data.get('revenue_dynamics_week', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[2], 8, format_currency(week_total), border=1, align='C', fill=True)

    month_total = direction_sum_data.get('revenue_dynamics_month', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[3], 8, format_currency(month_total), border=1, align='C', fill=True)

    year_total = direction_sum_data.get('revenue_dynamics_year', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[4], 8, format_currency(year_total), border=1, align='C', fill=True)

    pdf.add_page()
    pdf.set_font(font_name, 'B', 16)
    pdf.cell(0, 10, txt="Выручка по блюдам", ln=True, align='C')
    pdf.ln(5)

    product_sum_data = data[0].get('sum', {})

    col_widths = [120, 35, 34, 34, 34]
    headers = ["Продукт", "Выручка", "Выручка неделя", "Выручка месяц", "Выручка год"]

    # Заголовки таблицы
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1, align='C', fill=True)
    pdf.ln()

    # Данные таблицы
    pdf.set_font(font_name, '', 10)
    for product in data[0].get('data', []):
        label = product.get('label', '')
        if len(label) > 60:
            label = label[:57] + "..."

        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[0], 8, label, border=1, align='C')

        # Выручка
        pdf.cell(col_widths[1], 8, format_currency(product.get('revenue', 0)), border=1, align='C')

        # Выручка за неделю
        week_revenue = product.get('revenue_dynamics_week', 0)
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[2], 8, format_currency(week_revenue), border=1, align='C', fill=True)

        # Выручка за месяц
        month_revenue = product.get('revenue_dynamics_month', 0)
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[3], 8, format_currency(month_revenue), border=1, align='C', fill=True)

        # Выручка за год
        year_revenue = product.get('revenue_dynamics_year', 0)
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[4], 8, format_currency(year_revenue), border=1, align='C', fill=True)

        pdf.ln()

    # Итоговая строка
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    pdf.cell(col_widths[0], 8, product_sum_data.get('label', 'Итого'), border=1, align='C', fill=True)
    pdf.cell(col_widths[1], 8, format_currency(product_sum_data.get('revenue', 0)), border=1, align='C', fill=True)

    week_total = product_sum_data.get('revenue_dynamics_week', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[2], 8, format_currency(week_total), border=1, align='C', fill=True)

    month_total = product_sum_data.get('revenue_dynamics_month', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[3], 8, format_currency(month_total), border=1, align='C', fill=True)

    year_total = product_sum_data.get('revenue_dynamics_year', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[4], 8, format_currency(year_total), border=1, align='C', fill=True)

    pdf.add_page()
    pdf.set_font(font_name, 'B', 16)
    pdf.cell(0, 10, txt="Выручка по времени посещения", ln=True, align='C')
    pdf.ln(5)

    time_sum_data = data[0].get('sum', {})

    col_widths = [50, 40, 34, 34, 34]
    headers = ["Время", "Выручка", "Выручка неделя", "Выручка месяц", "Выручка год"]

    # Заголовки таблицы
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1, align='C', fill=True)
    pdf.ln()

    # Данные таблицы
    pdf.set_font(font_name, '', 10)
    for time_block in data[0].get('data', []):
        label = time_block.get('label', '')
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[0], 8, label, border=1, align='C')

        # Выручка
        pdf.cell(col_widths[1], 8, format_currency(time_block.get('revenue', 0)), border=1, align='C')

        # Выручка за неделю
        week_revenue = time_block.get('revenue_dynamics_week', 0)
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[2], 8, format_currency(week_revenue), border=1, align='C', fill=True)

        # Выручка за месяц
        month_revenue = time_block.get('revenue_dynamics_month', 0)
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[3], 8, format_currency(month_revenue), border=1, align='C', fill=True)

        # Выручка за год
        year_revenue = time_block.get('revenue_dynamics_year', 0)
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[4], 8, format_currency(year_revenue), border=1, align='C', fill=True)

        pdf.ln()

    # Итоговая строка
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    pdf.cell(col_widths[0], 8, time_sum_data.get('label', 'Итого'), border=1, align='C', fill=True)
    pdf.cell(col_widths[1], 8, format_currency(time_sum_data.get('revenue', 0)), border=1, align='C', fill=True)

    week_total = time_sum_data.get('revenue_dynamics_week', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[2], 8, format_currency(week_total), border=1, align='C', fill=True)

    month_total = time_sum_data.get('revenue_dynamics_month', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[3], 8, format_currency(month_total), border=1, align='C', fill=True)

    year_total = time_sum_data.get('revenue_dynamics_year') or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[4], 8, format_currency(year_total), border=1, align='C', fill=True)

    # Страница для анализа по дням недели
    pdf.add_page()
    pdf.set_font(font_name, 'B', 16)
    pdf.cell(0, 10, txt="Чеки по ценовым сегментам", ln=True, align='C')
    pdf.ln(5)

    weekday_sum_data = data[0].get('sum', {})

    col_widths = [50, 40, 34, 34, 34]
    headers = ["Ценовой сегмент", "Выручка", "Выручка неделя", "Выручка месяц", "Выручка год"]

    # Заголовки таблицы
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1, align='C', fill=True)
    pdf.ln()

    # Данные по дням
    pdf.set_font(font_name, '', 10)
    for day_block in data[0].get('data', []):
        label = day_block.get('label', '')
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[0], 8, label, border=1, align='C')

        pdf.cell(col_widths[1], 8, format_currency(day_block.get('revenue', 0)), border=1, align='C')

        week_revenue = day_block.get('revenue_dynamics_week', 0)
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[2], 8, format_currency(week_revenue), border=1, align='C', fill=True)

        month_revenue = day_block.get('revenue_dynamics_month', 0)
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[3], 8, format_currency(month_revenue), border=1, align='C', fill=True)

        year_revenue = day_block.get('revenue_dynamics_year', 0)
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[4], 8, format_currency(year_revenue), border=1, align='C', fill=True)

        pdf.ln()

    # Итоговая строка
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    pdf.cell(col_widths[0], 8, weekday_sum_data.get('label', 'Итого'), border=1, align='C', fill=True)
    pdf.cell(col_widths[1], 8, format_currency(weekday_sum_data.get('revenue', 0)), border=1, align='C', fill=True)

    week_total = weekday_sum_data.get('revenue_dynamics_week', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[2], 8, format_currency(week_total), border=1, align='C', fill=True)

    month_total = weekday_sum_data.get('revenue_dynamics_month', 0) or 0
    pdf.set_fill_color(*DEFAULT_COLOR)
    pdf.cell(col_widths[3], 8, format_percentage(month_total), border=1, align='C', fill=True)

    year_total = weekday_sum_data.get('revenue_dynamics_year') or 0
    fill_color = POSITIVE_COLOR if year_total >= 0 else NEGATIVE_COLOR
    pdf.set_fill_color(*fill_color)
    pdf.cell(col_widths[4], 8, format_percentage(year_total), border=1, align='C', fill=True)

    # Добавляем страницу и заголовок
    pdf.add_page()
    pdf.set_font(font_name, 'B', 16)
    pdf.cell(0, 10, txt="Выручка по дням недели", ln=True, align='C')
    pdf.ln(5)

    week_sum_data = data[0].get('sum', {})

    col_widths = [45, 40, 34, 34, 34]
    headers = ["День", "Выручка", "Динамика неделя", "Динамика месяц", "Динамика год"]

    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1, align='C', fill=True)
    pdf.ln()

    # Строки с данными
    pdf.set_font(font_name, '', 10)
    for weekday in data[0].get('data', []):
        label = weekday.get('label', '')
        revenue = weekday.get('revenue', 0)
        week_dyn = weekday.get('revenue_dynamics_week')
        month_dyn = weekday.get('revenue_dynamics_month')
        year_dyn = weekday.get('revenue_dynamics_year')

        # День
        pdf.set_fill_color(*DEFAULT_COLOR)
        pdf.cell(col_widths[0], 8, label, border=1, align='C')

        # Выручка
        pdf.cell(col_widths[1], 8, format_currency(revenue), border=1, align='C')

        # Неделя
        fill_color = POSITIVE_COLOR if week_dyn is not None and week_dyn >= 0 else NEGATIVE_COLOR
        pdf.set_fill_color(*fill_color)
        pdf.cell(col_widths[2], 8, format_percentage(week_dyn), border=1, align='C', fill=True)

        # Месяц
        fill_color = POSITIVE_COLOR if month_dyn is not None and month_dyn >= 0 else NEGATIVE_COLOR
        pdf.set_fill_color(*fill_color)
        pdf.cell(col_widths[3], 8, format_percentage(month_dyn), border=1, align='C', fill=True)

        # Год
        fill_color = POSITIVE_COLOR if year_dyn is not None and year_dyn >= 0 else NEGATIVE_COLOR
        pdf.set_fill_color(*fill_color)
        pdf.cell(col_widths[4], 8, format_percentage(year_dyn), border=1, align='C', fill=True)

        pdf.ln()

    # Итоговая строка
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    pdf.cell(col_widths[0], 8, week_sum_data.get('label', 'Итого'), border=1, align='C', fill=True)
    pdf.cell(col_widths[1], 8, format_currency(week_sum_data.get('revenue', 0)), border=1, align='C', fill=True)

    week_total = week_sum_data.get('revenue_dynamics_week', 0) or 0
    fill_color = POSITIVE_COLOR if week_total >= 0 else NEGATIVE_COLOR
    pdf.set_fill_color(*fill_color)
    pdf.cell(col_widths[2], 8, format_percentage(week_total), border=1, align='C', fill=True)

    month_total = week_sum_data.get('revenue_dynamics_month', 0) or 0
    fill_color = POSITIVE_COLOR if month_total >= 0 else NEGATIVE_COLOR
    pdf.set_fill_color(*fill_color)
    pdf.cell(col_widths[3], 8, format_percentage(month_total), border=1, align='C', fill=True)

    year_total = week_sum_data.get('revenue_dynamics_year', 0) or 0
    fill_color = POSITIVE_COLOR if year_total >= 0 else NEGATIVE_COLOR
    pdf.set_fill_color(*fill_color)
    pdf.cell(col_widths[4], 8, format_percentage(year_total), border=1, align='C', fill=True)

    pdf.add_page()
    pdf.set_font(font_name, 'B', 16)
    pdf.cell(0, 10, txt="Анализ работы официантов", ln=True, align='C')
    pdf.ln(5)

    staff_sum_data = data[0].get('sum', {})

    # Сводная информация
    pdf.set_font(font_name, '', 12)
    pdf.cell(0, 8, txt=f"Общая выручка: {format_currency(staff_sum_data.get('revenue', 0))}", ln=True)
    pdf.cell(0, 8, txt=f"Средняя выручка на сотрудника: {format_currency(staff_sum_data.get('avg_revenue', 0))}",
             ln=True)
    pdf.cell(0, 8, txt=f"Средний чек: {int(staff_sum_data.get('avg_checks', 0))}", ln=True)
    pdf.cell(0, 8, txt=f"Средняя глубина чека: {staff_sum_data.get('depth', 0):.2f}", ln=True)
    pdf.cell(0, 8, txt=f"Суммарный потенциал: {format_currency(staff_sum_data.get('potential', 0))}", ln=True)
    pdf.ln(10)

    col_widths = [70, 30, 34, 26, 25, 30]
    headers = ["Сотрудник", "Выручка", "Средняя выручка", "Глубина чека", "Глубина", "Потенциал"]

    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1, align='C', fill=True)
    pdf.ln()

    # Строки с данными
    pdf.set_font(font_name, '', 10)
    for staff in data[0].get('data', []):
        label = staff.get('label', '')
        revenue = staff.get('revenue', 0)
        avg_revenue = staff.get('avg_revenue', 0)
        avg_checks = staff.get('avg_checks', 0)
        depth = staff.get('depth', 0.0)
        potential = staff.get('potential', 0)

        pdf.set_fill_color(*DEFAULT_COLOR)

        # Имя
        pdf.cell(col_widths[0], 8, label, border=1, align='L')
        # Выручка
        pdf.cell(col_widths[1], 8, format_currency(revenue), border=1, align='C')
        # Средняя
        pdf.cell(col_widths[2], 8, format_currency(avg_revenue), border=1, align='C')
        # Чек
        pdf.cell(col_widths[3], 8, str(int(avg_checks)), border=1, align='C')
        # Глубина
        pdf.cell(col_widths[4], 8, f"{depth:.2f}", border=1, align='C')
        # Потенциал
        fill_color = POSITIVE_COLOR if potential >= 0 else NEGATIVE_COLOR
        pdf.set_fill_color(*fill_color)
        pdf.cell(col_widths[5], 8, format_currency(potential), border=1, align='C', fill=True)

        pdf.ln()

    # Итоговая строка
    pdf.set_font(font_name, 'B', 10)
    pdf.set_fill_color(*HEADER_COLOR)
    pdf.cell(col_widths[0], 8, staff_sum_data.get('label', 'Итого'), border=1, align='C', fill=True)
    pdf.cell(col_widths[1], 8, format_currency(staff_sum_data.get('revenue', 0)), border=1, align='C', fill=True)
    pdf.cell(col_widths[2], 8, format_currency(staff_sum_data.get('avg_revenue', 0)), border=1, align='C', fill=True)
    pdf.cell(col_widths[3], 8, str(int(staff_sum_data.get('avg_checks', 0))), border=1, align='C', fill=True)
    pdf.cell(col_widths[4], 8, f"{staff_sum_data.get('depth', 0):.2f}", border=1, align='C', fill=True)

    total_potential = staff_sum_data.get('potential', 0)
    fill_color = POSITIVE_COLOR if total_potential >= 0 else NEGATIVE_COLOR
    pdf.set_fill_color(*fill_color)
    pdf.cell(col_widths[5], 8, format_currency(total_potential), border=1, align='C', fill=True)

    pdf_output = BytesIO()
    pdf_output.write(pdf.output(dest='S').encode('latin-1'))  # ← сохраняем как байты
    pdf_output.seek(0)
    return pdf_output
