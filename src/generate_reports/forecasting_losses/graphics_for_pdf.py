import json
import logging
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile, FSInputFile

forecasting_losses_pdf_router = Router()

def check_font_path(font_path):
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Шрифт не найден по пути: {font_path}")


def get_first_non_null(*values):
    for value in values:
        if value is not None:
            return value
    return "-"


def get_first_non_null(*args):
    # Ваша реализация функции для получения первого не-null значения
    for arg in args:
        if arg is not None:
            return arg
    return "-"

def calculate_monthly_differences(store):
    """
    Вычисляет разницы между месяцами для магазина.
    Возвращает кортеж: (diff_price_1, diff_price_1_month, diff_price_2_month)
    """
    # Получаем значения разниц цен
    diff_price = store.get("diff_price")
    diff_price2 = store.get("diff_price2")
    diff_price3 = store.get("diff_price3")
    diff_price4 = store.get("diff_price4")

    # Первое изменение цены (первое не-null значение)
    diff_price_1 = get_first_non_null(diff_price, diff_price2, diff_price3, diff_price4)

    # Разница между 1 и 2 месяцами (diff_price3 - diff_price2)
    if isinstance(diff_price2, (int, float)) and isinstance(diff_price3, (int, float)):
        diff_price_1_month = round(diff_price3 - diff_price2, 2)
    else:
        diff_price_1_month = "-"

    # Разница между 2 и 3 месяцами (diff_price4 - diff_price3)
    if isinstance(diff_price3, (int, float)) and isinstance(diff_price4, (int, float)):
        diff_price_2_month = round(diff_price4 - diff_price3, 2)
    else:
        diff_price_2_month = "-"

    return diff_price_1, diff_price_1_month, diff_price_2_month


def create_pdf_with_table(data):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)

    try:
        check_font_path(r"C:\\WORK\\sova_rest_bot\\sova_rest_bot-master\\src\\basic\\revenue_analysis\\DejaVuSans.ttf")
    except FileNotFoundError as e:
        print(e)
        return None

    pdfmetrics.registerFont(TTFont('DejaVuSans',
                                   r"C:\\WORK\\sova_rest_bot\\sova_rest_bot-master\\src\\basic\\revenue_analysis\\DejaVuSans.ttf"))

    elements = []
    title_style = ParagraphStyle(name='TitleStyle', fontName='DejaVuSans', fontSize=16, alignment=1)
    title = Paragraph("Прогнозирование потерь", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Заголовок таблицы
    table_data = [["Магазин", "Прогноз", "Первое изменение цены", "Изменение (1 месяц)", "Изменение (2 месяца)"]]

    # Сортировка магазинов по убыванию прогноза
    sorted_data = sorted(data["data"], key=lambda store: store.get("forecast", 0), reverse=True)

    for store in sorted_data:
        forecast = store.get("forecast", "-")

        # Вычисляем разницы между месяцами
        diff_price_1, diff_price_1_month, diff_price_2_month = calculate_monthly_differences(store)

        # Пропускаем магазин, если нет данных о разнице цен
        if diff_price_1 == "-" and diff_price_1_month == "-" and diff_price_2_month == "-":
            continue

        # Добавляем строку в таблицу
        table_data.append([
            store["label"],
            f"{forecast:,.2f}" if isinstance(forecast, (int, float)) else forecast,
            f"{diff_price_1:,.2f}" if isinstance(diff_price_1, (int, float)) else "-",
            f"{diff_price_1_month:,.2f}" if isinstance(diff_price_1_month, (int, float)) else "-",
            f"{diff_price_2_month:,.2f}" if isinstance(diff_price_2_month, (int, float)) else "-"
        ])

    # Создаем таблицу
    table = Table(table_data, colWidths=[2.5 * inch, 0.7 * inch, 1.7 * inch, 1.4 * inch, 1.4 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)

    # Собираем PDF
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer


def save_pdf(pdf_buffer):
    try:
        with open("loss_forecast_report.pdf", "wb") as f:
            f.write(pdf_buffer.read())
        print("PDF успешно сохранен.")
    except Exception as e:
        print(f"Ошибка при сохранении PDF: {e}")


def load_json_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except Exception as e:
        print(f"Ошибка загрузки данных JSON из {file_path}: {e}")
        return None


def load_revenue_data(filepath: str) -> dict:
    """Загружает данные из JSON-файла."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Ошибка при чтении файла {filepath}: {e}")
        return {}


@forecasting_losses_pdf_router.callback_query(F.data == "format_pdf_loss_forecast")
async def handle_forecasting_losses_pdf(callback_query: CallbackQuery):
    """Обработчик для кнопки 'Сформировать PDF отчёт по прогнозированию потерь'."""
    # Отвечаем на callback_query, чтобы убрать "часики" у кнопки
    await callback_query.answer("Формирую PDF отчёт по прогнозированию потерь...")

    # Извлекаем тип отчёта из callback_data
    report_type = callback_query.data.split("_")[-1]

    # Загрузка данных из JSON-файла
    filepath = r"C:\WORK\sova_rest_bot\sova_rest_bot-master\files\jsons_for_reports\loss-forecast_data_example.json"
    loss_forecast_data = load_revenue_data(filepath)  # Используем ту же функцию для загрузки данных

    if not loss_forecast_data:
        await callback_query.message.answer("Ошибка при загрузке данных для отчёта.")
        return

    # Создание PDF
    try:
        pdf_buffer = create_pdf_with_table(loss_forecast_data)  # Используем существующую функцию
    except Exception as e:
        logging.error(f"Ошибка при создании PDF: {e}")
        await callback_query.message.answer("Ошибка при создании PDF-отчёта.")
        return

    # Отправка PDF пользователю
    try:
        # Создаём объект BufferedInputFile для отправки PDF
        input_file = BufferedInputFile(pdf_buffer.getvalue(), filename=f"loss_forecast_{report_type}.pdf")

        # Отправляем документ пользователю
        await callback_query.message.answer_document(
            input_file,
            caption=f"Ваш отчёт по прогнозированию потерь (тип: {report_type}):"
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке PDF: {e}")
        await callback_query.message.answer("Ошибка при отправке отчёта.")