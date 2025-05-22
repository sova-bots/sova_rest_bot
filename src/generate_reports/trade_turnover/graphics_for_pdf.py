import json
import logging
import os

import matplotlib.pyplot as plt
from io import BytesIO

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InputFile, BufferedInputFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab import pdfbase
from sympy.parsing.sympy_parser import null


trade_turnover_pdf_router = Router()

def create_combined_graph(data):
    # Извлекаем информацию из данных с правильными ключами, заменяя None на 0
    labels = [store["label"] for store in data["data"]]
    turnover_week = [store.get("turnover_in_days_week", 0) or 0 for store in data["data"]]
    turnover_month = [store.get("turnover_in_days_month", 0) or 0 for store in data["data"]]
    turnover_year = [store.get("turnover_in_days_year", 0) or 0 for store in data["data"]]

    # Определяем цвета для каждого периода
    week_color = (255 / 255, 226 / 255, 13 / 255)  # RGB (255,226,13) -> Yellow
    month_color = (214 / 255, 154 / 255, 129 / 255)  # RGB (214,154,129) -> Light Brown
    year_color = (197 / 255, 227 / 255, 132 / 255)  # RGB (197,227,132) -> Light Green

    # Создаем общий график с 3 строками
    fig = plt.figure(figsize=(16, 18))  # Общий размер фигуры
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1])  # 3 строки, 2 столбца

    # Первый ряд: столбчатая диаграмма
    ax0 = fig.add_subplot(gs[0, :])  # Первая строка, весь столбец
    bar_width = 0.25  # Ширина столбцов
    index = range(len(labels))

    ax0.bar([i - bar_width for i in index], turnover_week, width=bar_width, label="Выручка за неделю", color=week_color)
    ax0.bar([i for i in index], turnover_month, width=bar_width, label="Выручка за месяц", color=month_color)
    ax0.bar([i + bar_width for i in index], turnover_year, width=bar_width, label="Выручка за год", color=year_color)
    ax0.set_xticks(index)
    ax0.set_xticklabels(labels, rotation=45, ha="right")
    ax0.set_xlabel("Магазины")
    ax0.set_ylabel("Выручка")
    ax0.set_title("Анализ выручки по периодам (Столбчатая диаграмма)")
    ax0.legend()
    ax0.grid(True, axis='y')

    # Второй и третий ряды: круговые диаграммы
    num_stores = len(data["data"])
    stores_per_row = 2  # 2 магазина в ряду, чтобы они не сливались

    for i in range(num_stores):
        sizes = [turnover_week[i], turnover_month[i], turnover_year[i]]
        labels_pie = ["Выручка за неделю", "Выручка за месяц", "Выручка за год"]

        row = (i // stores_per_row) + 1  # Второй или третий ряд
        col = i % stores_per_row  # Столбец в пределах ряда

        if row < 3:  # Поскольку у нас всего 3 ряда
            ax = fig.add_subplot(gs[row, col])
            ax.pie(sizes, labels=labels_pie, autopct='%1.1f%%', startangle=90,
                   colors=[week_color, month_color, year_color])
            ax.set_title(f"{labels[i]}")
            ax.axis('equal')  # Чтобы круговая диаграмма была круглой

    # Убираем пустые подграфики, если количество магазинов нечетное
    if num_stores % stores_per_row != 0:
        fig.delaxes(fig.add_subplot(gs[2, 1]))  # Удаляем пустой подграфик

    fig.suptitle("Анализ выручки по периодам", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])  # Регулируем отступы

    # Сохраняем график в BytesIO
    img_bytes = BytesIO()
    plt.savefig(img_bytes, format='png')
    plt.close()

    img_bytes.seek(0)
    return img_bytes


def create_pdf_with_table_and_graphs(data, graph_bytes):
    # Создаём PDF-документ
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)

    # Регистрируем шрифт
    pdfmetrics.registerFont(
        TTFont('FreeSerif', r"C:\WORK\sova_rest_bot\sova_rest_bot-master\src\basic\revenue_analysis\FreeSerif.ttf"))

    elements = []

    # Заголовок документа с новым шрифтом
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='TitleStyle', fontName='FreeSerif', fontSize=16, alignment=1)
    title = Paragraph("СЕБЕСТОИМОСТЬ ПРОДУКТОВ", title_style)
    elements.append(title)

    # Добавляем пустое пространство перед таблицей
    elements.append(Spacer(1, 12))

    # Создаём таблицу
    table_data = [["Магазин", "Выручка за неделю", "Выручка за месяц", "Выручка за год"]]
    for store in data["data"]:
        turnover_week = store.get('turnover_in_days_week', 0) or 0
        turnover_month = store.get('turnover_in_days_month', 0) or 0
        turnover_year = store.get('turnover_in_days_year', 0) or 0

        # Форматирование чисел с разделением по запятым
        table_data.append([store["label"], f"{turnover_week:,.2f}", f"{turnover_month:,.2f}", f"{turnover_year:,.2f}"])

    table = Table(table_data, colWidths=[2.5 * inch, 1.8 * inch, 1.8 * inch, 1.8 * inch])  # Увеличили ширину столбцов
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Заголовок таблицы
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Выравнивание по центру
        ('FONTNAME', (0, 0), (-1, -1), 'FreeSerif'),  # Задаем шрифт для всей таблицы!
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # Размер шрифта
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Отступ снизу для заголовка
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Цвет фона строк
        ('GRID', (0, 0), (-1, -1), 1, colors.black)  # Сетка таблицы
    ]))
    elements.append(table)

    # Добавляем пустое пространство перед графиком
    elements.append(Spacer(1, 12))

    # Добавляем график
    graph_image = Image(graph_bytes, width=6.5 * inch, height=7.5 * inch)
    elements.append(graph_image)

    # Собираем PDF
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer


# Функция загрузки данных из JSON
def load_revenue_data(filepath: str) -> dict:
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Ошибка при чтении файла {filepath}: {e}")
        return {}


@trade_turnover_pdf_router.callback_query(F.data == "format_pdf_turnover")
async def generate_report(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик для кнопки 'Сформировать PDF отчёт по товарообороту'."""
    # Отвечаем на callback_query, чтобы убрать "часики" у кнопки
    await callback_query.answer("Формирую PDF отчёт по товарообороту...")

    # Извлекаем тип отчёта из callback_data
    report_type = callback_query.data.split("_")[-1]

    # Загрузка данных из JSON-файла
    filepath = r"C:\WORK\sova_rest_bot\sova_rest_bot-master\files\jsons_for_reports\turnover-store_example.json"
    turnover_data = load_revenue_data(filepath)  # Используем ту же функцию для загрузки данных

    if not turnover_data:
        await callback_query.message.answer("Ошибка при загрузке данных для отчёта.")
        return

    # Генерация графика
    try:
        graph_bytes = create_combined_graph(turnover_data)
    except Exception as e:
        logging.error(f"Ошибка при создании графика: {e}")
        await callback_query.message.answer("Ошибка при создании графика для отчёта.")
        return

    # Создание PDF
    try:
        pdf_buffer = create_pdf_with_table_and_graphs(turnover_data, graph_bytes)
    except Exception as e:
        logging.error(f"Ошибка при создании PDF: {e}")
        await callback_query.message.answer("Ошибка при создании PDF-отчёта.")
        return

    # Отправка PDF пользователю
    try:
        # Создаём объект BufferedInputFile для отправки PDF
        input_file = BufferedInputFile(pdf_buffer.getvalue(), filename=f"trade_turnover_{report_type}.pdf")

        # Отправляем документ пользователю
        await callback_query.message.answer_document(
            input_file,
            caption=f"Ваш отчёт по товарообороту (тип: {report_type}):"
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке PDF: {e}")
        await callback_query.message.answer("Ошибка при отправке отчёта.")

