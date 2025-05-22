import logging
from io import BytesIO
import seaborn as sns
import json
import matplotlib.pyplot as plt
from aiogram import F
from aiogram import Router
from aiogram.types import CallbackQuery, BufferedInputFile
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
from reportlab.lib.units import inch


analys_revenue_pdf_router = Router()


def create_combined_graph(data):
    # Extract information from JSON
    labels = [store["label"] for store in data["data"]]
    revenue_week = [store["revenue_week"] for store in data["data"]]
    revenue_month = [store["revenue_month"] for store in data["data"]]
    revenue_year = [store["revenue_year"] for store in data["data"]]

    # Define custom colors
    week_color = (255 / 255, 226 / 255, 13 / 255)  # RGB (255,226,13) -> Yellow
    month_color = (214 / 255, 154 / 255, 129 / 255)  # RGB (214,154,129) -> Light Brown
    year_color = (197 / 255, 227 / 255, 132 / 255)  # RGB (197,227,132) -> Light Green

    # Create a combined figure with 3 rows
    fig = plt.figure(figsize=(16, 18))  # Общий размер фигуры
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1])  # 3 строки, 2 столбца

    # Первый ряд: столбчатая диаграмма
    ax0 = fig.add_subplot(gs[0, :])  # Первая строка, весь столбец
    bar_width = 0.25  # Ширина столбцов
    index = range(len(labels))

    ax0.bar([i - bar_width for i in index], revenue_week, width=bar_width, label="Выручка за неделю",
            color=week_color)
    ax0.bar([i for i in index], revenue_month, width=bar_width, label="Выручка за месяц", color=month_color)
    ax0.bar([i + bar_width for i in index], revenue_year, width=bar_width, label="Выручка за год",
            color=year_color)
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

    for i, store in enumerate(data["data"]):
        sizes = [store["revenue_week"], store["revenue_month"], store["revenue_year"]]
        labels_pie = ["Выручка за неделю", "Выручка за месяц", "Выручка за год"]

        # Определяем, в каком ряду и столбце будет диаграмма
        row = (i // stores_per_row) + 1  # Второй или третий ряд
        col = i % stores_per_row  # Столбец в пределах ряда

        # Создаем подграфик для круговой диаграммы
        ax = fig.add_subplot(gs[row, col])  # Разделяем на два столбца
        ax.pie(sizes, labels=labels_pie, autopct='%1.1f%%', startangle=90,
               colors=[week_color, month_color, year_color])
        ax.set_title(f"{store['label']}")
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
    try:
        pdfmetrics.registerFont(TTFont('DejaVuSans', r"C:\WORK\sova_rest_bot\sova_rest_bot-master\src\basic\revenue_analysis\DejaVuSans.ttf"))
        print("Шрифт FreeSerif успешно зарегистрирован!")
    except Exception as e:
        print(f"Ошибка при регистрации шрифта: {e}")

    """Создаёт PDF с таблицей, графиками и заголовком."""
    # Создаём PDF-документ
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    elements = []

    # Заголовок документа
    styles = getSampleStyleSheet()
    styles['Title'].fontName = 'DejaVuSans'  # Используем встроенный шрифт Helvetica
    title = Paragraph("АНАЛИЗ ВЫРУЧКИ", styles['Title'])
    elements.append(title)

    # Создаём таблицу
    table_data = [
        ["Магазин", "Выручка за неделю", "Выручка за месяц", "Выручка за год"]
    ]
    for store in data["data"]:
        table_data.append([
            store["label"],
            f"{store['revenue_week']:,}",
            f"{store['revenue_month']:,}",
            f"{store['revenue_year']:,}"
        ])

    # Создаём объект таблицы
    table = Table(table_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])  # Уменьшаем ширину столбцов
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Заголовок таблицы
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Выравнивание по центру
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),  # Задаем шрифт для всей таблицы!
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # Размер шрифта
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Отступ снизу для заголовка
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Цвет фона строк
        ('GRID', (0, 0), (-1, -1), 1, colors.black)  # Сетка таблицы
    ]))
    elements.append(table)

    # Добавляем график
    graph_image = Image(graph_bytes, width=6 * inch, height=7 * inch)
    elements.append(graph_image)

    # Собираем PDF
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer


def load_revenue_data(filepath: str) -> dict:
    """Загружает данные из JSON-файла."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Ошибка при чтении файла {filepath}: {e}")
        return {}


@analys_revenue_pdf_router.callback_query(F.data == "revenue_analysis_pdf")
async def handle_format_pdf(callback_query: CallbackQuery):
    """Обработчик для кнопки 'Сформировать PDF отчёт'."""
    # Отвечаем на callback_query, чтобы убрать "часики" у кнопки
    await callback_query.answer("Формирую PDF отчёт...")

    # Извлекаем тип отчёта из callback_data
    report_type = callback_query.data.split("_")[-1]

    # Загрузка данных из JSON-файла
    filepath = r"C:\WORK\sova_rest_bot\sova_rest_bot-master\files\jsons_for_reports\revenue analys.json"
    revenue_data = load_revenue_data(filepath)

    if not revenue_data:
        await callback_query.message.answer("Ошибка при загрузке данных для отчёта.")
        return

    # Генерация графика
    try:
        graph_bytes = create_combined_graph(revenue_data)
    except Exception as e:
        logging.error(f"Ошибка при создании графика: {e}")
        await callback_query.message.answer("Ошибка при создании графика для отчёта.")
        return

    # Создание PDF
    try:
        pdf_buffer = create_pdf_with_table_and_graphs(revenue_data, graph_bytes)
    except Exception as e:
        logging.error(f"Ошибка при создании PDF: {e}")
        await callback_query.message.answer("Ошибка при создании PDF-отчёта.")
        return

    # Отправка PDF пользователю
    try:
        # Создаём объект BufferedInputFile для отправки PDF
        input_file = BufferedInputFile(pdf_buffer.getvalue(), filename=f"revenue_analysis_{report_type}.pdf")

        # Отправляем документ пользователю
        await callback_query.message.answer_document(
            input_file,
            caption=f"Ваш отчёт по анализу выручки (тип: {report_type}):"
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке PDF: {e}")
        await callback_query.message.answer("Ошибка при отправке отчёта.")

