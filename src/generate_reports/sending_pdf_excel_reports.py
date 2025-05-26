import logging
import os
import tempfile
import json
from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from src.analytics.handlers.types.msg_data import MsgData
from src.generate_reports.food_cost.food_cost_pdf import create_pdf_report_for_food_cost, \
    create_pdf_report_for_food_cost_analysis
from src.generate_reports.loss_forecast.loss_forecast_excel import loss_forecast_only_negative_create_excel_report
from src.generate_reports.losses.losses_excel import losses_only_negative_create_excel_report
from src.generate_reports.losses.losses_pdf import losses_parameters_create_pdf_report, \
    losses_only_negative_create_pdf_report
from src.generate_reports.markup.markup_pdf import create_pdf_report_for_markup, create_pdf_report_for_markup_analysis
from src.generate_reports.report_link import REPORT_GENERATORS
from src.generate_reports.revenue_analysis.revenue_excel import revenue_parameters_create_excel_report_analysis
from src.generate_reports.revenue_analysis.revenue_pdf import (
    revenue_parameters_create_pdf_report, revenue_parameters_create_pdf_report_analysis
)
from src.analytics.handlers.msg.headers import make_header
from src.generate_reports.turnover.turnover_pdf import create_pdf_report_for_turnover, \
    create_pdf_report_for_turnover_analysis
from src.generate_reports.write_off.write_off_excel import write_off_parameters_create_excel_report
from src.generate_reports.write_off.write_off_pdf import write_off_parameters_create_pdf_report

from src.analytics.handlers.msg.msg_util import report_keyboard

file_report_router = Router()


@file_report_router.callback_query(F.data == "report:send_pdf_report")
async def handle_send_pdf_report(callback: CallbackQuery, state: FSMContext):
    await state.update_data({"report:delivery_format": "pdf"})
    msg_data = MsgData(msg=callback.message, state=state, tgid=callback.from_user.id)
    await send_generated_report(callback, msg_data)  # Отправка PDF отчёта напрямую

@file_report_router.callback_query(F.data == "report:send_excel_report")
async def handle_send_excel_report(callback: CallbackQuery, state: FSMContext):
    await state.update_data({"report:delivery_format": "excel"})
    msg_data = MsgData(msg=callback.message, state=state, tgid=callback.from_user.id)
    await send_generated_report(callback, msg_data)  # Отправка Excel отчёта напрямую


@file_report_router.callback_query(F.data.startswith("report:send_"))
async def handle_send_any_report(callback: CallbackQuery, state: FSMContext):
    msg_data = MsgData(
        msg=callback.message,
        state=state,
        tgid=callback.from_user.id
    )
    await send_generated_report(callback, msg_data)


# PDF
async def generate_revenue_pdf(callback: CallbackQuery, msg_data: MsgData):
    from src.generate_reports.revenue_analysis.revenue_pdf import revenue_parameters_create_pdf_report

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 PDF отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        pdf_buffer = revenue_parameters_create_pdf_report(json_data)
        pdf_path = os.path.join(tempfile.gettempdir(), "revenue.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_buffer.read())

        await callback.message.answer_document(FSInputFile(pdf_path), caption=caption)

    except Exception as e:
        await callback.message.answer(f"Ошибка при создании PDF: {e}")

# Excel
async def generate_revenue_excel(callback: CallbackQuery, msg_data: MsgData):
    from src.generate_reports.revenue_analysis.revenue_excel import create_revenue_excel, load_revenue_data

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 Excel отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        revenue_data = load_revenue_data(json_file_path)
        excel_path = os.path.join(tempfile.gettempdir(), "revenue.xlsx")
        create_revenue_excel(revenue_data, excel_path)

        await callback.message.answer_document(
            FSInputFile(excel_path),
            caption=caption,
            reply_markup=report_keyboard
        )

    except Exception as e:
        await callback.message.answer(f"Ошибка при создании Excel: {e}")
    finally:
        cleanup_temp([json_file_path, excel_path])


async def generate_revenue_analysis_pdf(callback: CallbackQuery, msg_data: MsgData):

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 PDF отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        pdf_buffer = revenue_parameters_create_pdf_report_analysis(json_data)
        pdf_path = os.path.join(tempfile.gettempdir(), "revenue_analysis.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_buffer.read())

        await callback.message.answer_document(
            FSInputFile(pdf_path),
            caption=caption,
            reply_markup=report_keyboard
        )

    except Exception as e:
        await callback.message.answer(f"Ошибка при создании PDF: {e}")


async def generate_revenue_analysis_excel(callback: CallbackQuery, msg_data: MsgData):

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 Excel отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        excel_buffer = revenue_parameters_create_excel_report_analysis(json_data)
        excel_path = os.path.join(tempfile.gettempdir(), "revenue_analysis.xlsx")

        with open(excel_path, "wb") as out_file:
            out_file.write(excel_buffer.read())

        await callback.message.answer_document(
            document=FSInputFile(excel_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации Excel по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")

async def generate_inventory_parameters_pdf(callback: CallbackQuery, msg_data: MsgData):
    from src.generate_reports.inventory.inventory_pdf import inventory_parameters_create_pdf_report

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 PDF отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        pdf_buffer = inventory_parameters_create_pdf_report(json_data)

        pdf_path = os.path.join(tempfile.gettempdir(), "inventory_report.pdf")
        with open(pdf_path, "wb") as out_file:
            out_file.write(pdf_buffer.getvalue())

        await callback.message.answer_document(
            document=FSInputFile(pdf_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации PDF по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def generate_inventory_parameters_excel(callback: CallbackQuery, msg_data: MsgData):
    from src.generate_reports.inventory.inventory_excel import create_excel_report  # Import here

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 Excel отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        excel_buffer = create_excel_report(json_data)
        excel_path = os.path.join(tempfile.gettempdir(), "inventory_report.xlsx")

        with open(excel_path, "wb") as out_file:
            out_file.write(excel_buffer.read())

        await callback.message.answer_document(
            document=FSInputFile(excel_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации Excel по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def generate_write_off_parameters_pdf(callback: CallbackQuery, msg_data: MsgData):
    """Генерация и отправка PDF отчёта по потерям товаров."""

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 PDF отчёт прикреплён."

    try:
        # Получение пути к JSON файлу
        json_file_path = await ensure_json_file(state_data, msg_data)

        # Чтение данных из JSON
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # Генерация PDF отчёта
        pdf_buffer = write_off_parameters_create_pdf_report(json_data)

        # Сохранение PDF в временный файл
        pdf_path = os.path.join(tempfile.gettempdir(), "write_off.pdf")
        with open(pdf_path, "wb") as out_file:
            out_file.write(pdf_buffer.getvalue())

        # Отправка PDF отчёта пользователю через Telegram
        await callback.message.answer_document(
            document=FSInputFile(pdf_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации PDF по потерям товаров: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")

async def generate_write_off_parameters_excel(callback: CallbackQuery, msg_data: MsgData):

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 Excel отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        excel_buffer = write_off_parameters_create_excel_report(json_data)
        excel_path = os.path.join(tempfile.gettempdir(), "write_off.xlsx")

        with open(excel_path, "wb") as out_file:
            out_file.write(excel_buffer.read())

        await callback.message.answer_document(
            document=FSInputFile(excel_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации Excel по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")

async def generate_losses_parameters_pdf(callback: CallbackQuery, msg_data: MsgData):
    """Генерация и отправка PDF отчёта по потерям товаров."""

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 PDF отчёт прикреплён."

    try:
        # Получение пути к JSON файлу
        json_file_path = await ensure_json_file(state_data, msg_data)

        # Чтение данных из JSON
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # Генерация PDF отчёта
        pdf_buffer = losses_parameters_create_pdf_report(json_data)

        # Сохранение PDF в временный файл
        pdf_path = os.path.join(tempfile.gettempdir(), "losses_report.pdf")
        with open(pdf_path, "wb") as out_file:
            out_file.write(pdf_buffer.getvalue())

        # Отправка PDF отчёта пользователю через Telegram
        await callback.message.answer_document(
            document=FSInputFile(pdf_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации PDF по потерям товаров: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def generate_losses_parameters_excel(callback: CallbackQuery, msg_data: MsgData):
    from src.generate_reports.losses.losses_excel import losses_parameters_create_excel_report  # Import here

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 Excel отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        excel_buffer = losses_parameters_create_excel_report(json_data)
        excel_path = os.path.join(tempfile.gettempdir(), "losses_report.xlsx")

        with open(excel_path, "wb") as out_file:
            out_file.write(excel_buffer.read())

        await callback.message.answer_document(
            document=FSInputFile(excel_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации Excel по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def generate_losses_only_negative_pdf(callback: CallbackQuery, msg_data: MsgData):
    """Генерация и отправка PDF отчёта по потерям товаров."""

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 PDF отчёт прикреплён."

    try:
        # Получение пути к JSON файлу
        json_file_path = await ensure_json_file(state_data, msg_data)

        # Чтение данных из JSON
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # Генерация PDF отчёта
        pdf_buffer = losses_only_negative_create_pdf_report(json_data)

        # Сохранение PDF в временный файл
        pdf_path = os.path.join(tempfile.gettempdir(), "losses_report.pdf")
        with open(pdf_path, "wb") as out_file:
            out_file.write(pdf_buffer.getvalue())

        # Отправка PDF отчёта пользователю через Telegram
        await callback.message.answer_document(
            document=FSInputFile(pdf_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации PDF по потерям товаров: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def generate_losses_only_negative_excel(callback: CallbackQuery, msg_data: MsgData):
    from src.generate_reports.losses.losses_excel import losses_parameters_create_excel_report  # Import here

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 Excel отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        excel_buffer = losses_only_negative_create_excel_report(json_data)
        excel_path = os.path.join(tempfile.gettempdir(), "losses_report.xlsx")

        with open(excel_path, "wb") as out_file:
            out_file.write(excel_buffer.read())

        await callback.message.answer_document(
            document=FSInputFile(excel_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации Excel по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")

async def generate_loss_forecast_parameters_pdf(callback: CallbackQuery, msg_data: MsgData):
    from src.generate_reports.loss_forecast.loss_forecast_pdf import loss_forecast_create_pdf_report

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 PDF отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        pdf_buffer = loss_forecast_create_pdf_report(json_data)

        pdf_path = os.path.join(tempfile.gettempdir(), "loss_forecast.pdf")
        with open(pdf_path, "wb") as out_file:
            out_file.write(pdf_buffer.getvalue())

        await callback.message.answer_document(
            document=FSInputFile(pdf_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации PDF по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def generate_loss_forecast_parameters_excel(callback: CallbackQuery, msg_data: MsgData):
    from src.generate_reports.loss_forecast.loss_forecast_excel import loss_forecast_create_excel_report

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 Excel отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        excel_buffer = loss_forecast_create_excel_report(json_data)
        excel_path = os.path.join(tempfile.gettempdir(), "loss_forecast.xlsx")

        with open(excel_path, "wb") as out_file:
            out_file.write(excel_buffer.read())

        await callback.message.answer_document(
            document=FSInputFile(excel_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации Excel по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def generate_loss_forecast_only_negative_pdf(callback: CallbackQuery, msg_data: MsgData):
    from src.generate_reports.loss_forecast.loss_forecast_pdf import loss_forecast_create_pdf_report

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 PDF отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        pdf_buffer = loss_forecast_create_pdf_report(json_data)

        pdf_path = os.path.join(tempfile.gettempdir(), "loss_forecast.pdf")
        with open(pdf_path, "wb") as out_file:
            out_file.write(pdf_buffer.getvalue())

        await callback.message.answer_document(
            document=FSInputFile(pdf_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации PDF по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def generate_loss_forecast_only_negative_excel(callback: CallbackQuery, msg_data: MsgData):
    from src.generate_reports.loss_forecast.loss_forecast_excel import loss_forecast_create_excel_report

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 Excel отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        excel_buffer = loss_forecast_only_negative_create_excel_report(json_data)
        excel_path = os.path.join(tempfile.gettempdir(), "loss_forecast.xlsx")

        with open(excel_path, "wb") as out_file:
            out_file.write(excel_buffer.read())

        await callback.message.answer_document(
            document=FSInputFile(excel_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации Excel по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")

async def generate_food_cost_parameters_pdf(callback: CallbackQuery, msg_data: MsgData):

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 PDF отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        pdf_buffer = create_pdf_report_for_food_cost(json_data)

        pdf_path = os.path.join(tempfile.gettempdir(), "foodcost.pdf")
        with open(pdf_path, "wb") as out_file:
            out_file.write(pdf_buffer.getvalue())

        await callback.message.answer_document(
            document=FSInputFile(pdf_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации PDF по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def generate_food_cost_parameters_excel(callback: CallbackQuery, msg_data: MsgData):
    from src.generate_reports.food_cost.food_cost_excel import create_excel_report_for_food_cost

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 Excel отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        excel_buffer = create_excel_report_for_food_cost(json_data)
        excel_path = os.path.join(tempfile.gettempdir(), "foodcost.xlsx")

        with open(excel_path, "wb") as out_file:
            out_file.write(excel_buffer.read())

        await callback.message.answer_document(
            document=FSInputFile(excel_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации Excel по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def generate_food_cost_analysis_pdf(callback: CallbackQuery, msg_data: MsgData):

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 PDF отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        pdf_buffer = create_pdf_report_for_food_cost_analysis(json_data)

        pdf_path = os.path.join(tempfile.gettempdir(), "foodcost_analysis.pdf")
        with open(pdf_path, "wb") as out_file:
            out_file.write(pdf_buffer.getvalue())

        await callback.message.answer_document(
            document=FSInputFile(pdf_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации PDF по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def generate_food_cost_analysis_excel(callback: CallbackQuery, msg_data: MsgData):
    from src.generate_reports.food_cost.food_cost_excel import create_excel_report_for_food_cost_analysis

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 Excel отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        excel_buffer = create_excel_report_for_food_cost_analysis(json_data)
        excel_path = os.path.join(tempfile.gettempdir(), "foodcost_analysis.xlsx")

        with open(excel_path, "wb") as out_file:
            out_file.write(excel_buffer.read())

        await callback.message.answer_document(
            document=FSInputFile(excel_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации Excel по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def generate_markup_parameters_pdf(callback: CallbackQuery, msg_data: MsgData):

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 PDF отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        pdf_buffer = create_pdf_report_for_markup(json_data)

        pdf_path = os.path.join(tempfile.gettempdir(), "markup.pdf")
        with open(pdf_path, "wb") as out_file:
            out_file.write(pdf_buffer.getvalue())

        await callback.message.answer_document(
            document=FSInputFile(pdf_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации PDF по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")

async def generate_markup_parameters_excel(callback: CallbackQuery, msg_data: MsgData):
    from src.generate_reports.markup.markup_excel import create_excel_report_for_markup

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 Excel отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        excel_buffer = create_excel_report_for_markup(json_data)
        excel_path = os.path.join(tempfile.gettempdir(), "markup.xlsx")

        with open(excel_path, "wb") as out_file:
            out_file.write(excel_buffer.read())

        await callback.message.answer_document(
            document=FSInputFile(excel_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации Excel по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")

async def generate_markup_analysis_pdf(callback: CallbackQuery, msg_data: MsgData):

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 PDF отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        pdf_buffer = create_pdf_report_for_markup_analysis(json_data)

        pdf_path = os.path.join(tempfile.gettempdir(), "markup_analysis.pdf")
        with open(pdf_path, "wb") as out_file:
            out_file.write(pdf_buffer.getvalue())

        await callback.message.answer_document(
            document=FSInputFile(pdf_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации PDF по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def generate_markup_analysis_excel(callback: CallbackQuery, msg_data: MsgData):
    from src.generate_reports.markup.markup_excel import create_excel_report_for_markup_analysis

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 Excel отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        excel_buffer = create_excel_report_for_markup_analysis(json_data)
        excel_path = os.path.join(tempfile.gettempdir(), "markup_analysis.xlsx")

        with open(excel_path, "wb") as out_file:
            out_file.write(excel_buffer.read())

        await callback.message.answer_document(
            document=FSInputFile(excel_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации Excel по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def generate_turnover_parameters_pdf(callback: CallbackQuery, msg_data: MsgData):

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 PDF отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        pdf_buffer = create_pdf_report_for_turnover(json_data)

        pdf_path = os.path.join(tempfile.gettempdir(), "turnover.pdf")
        with open(pdf_path, "wb") as out_file:
            out_file.write(pdf_buffer.getvalue())

        await callback.message.answer_document(
            document=FSInputFile(pdf_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации PDF по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def generate_turnover_analysis_pdf(callback: CallbackQuery, msg_data: MsgData):

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 PDF отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        pdf_buffer = create_pdf_report_for_turnover_analysis(json_data)

        pdf_path = os.path.join(tempfile.gettempdir(), "turnover_analysis.pdf")
        with open(pdf_path, "wb") as out_file:
            out_file.write(pdf_buffer.getvalue())

        await callback.message.answer_document(
            document=FSInputFile(pdf_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации PDF по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def generate_turnover_analysis_excel(callback: CallbackQuery, msg_data: MsgData):
    from src.generate_reports.turnover.turnover_excel import create_excel_report_for_turnover_analysis

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 Excel отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        excel_buffer = create_excel_report_for_turnover_analysis(json_data)
        excel_path = os.path.join(tempfile.gettempdir(), "turnover_analysis.xlsx")

        with open(excel_path, "wb") as out_file:
            out_file.write(excel_buffer.read())

        await callback.message.answer_document(
            document=FSInputFile(excel_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации Excel по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def generate_turnover_parameters_excel(callback: CallbackQuery, msg_data: MsgData):
    from src.generate_reports.turnover.turnover_excel import create_excel_report_for_turnover

    state_data = await msg_data.state.get_data()
    header = await make_header(msg_data)
    caption = f"{header}\n\n📎 Excel отчёт прикреплён."

    try:
        json_file_path = await ensure_json_file(state_data, msg_data)
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        excel_buffer = create_excel_report_for_turnover(json_data)
        excel_path = os.path.join(tempfile.gettempdir(), "turnover.xlsx")

        with open(excel_path, "wb") as out_file:
            out_file.write(excel_buffer.read())

        await callback.message.answer_document(
            document=FSInputFile(excel_path),
            caption=caption,
            reply_markup=report_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при генерации Excel по инвентаризации: {e}")
        await callback.message.answer("Произошла ошибка при формировании отчёта.")


async def ensure_json_file(state_data: dict, msg_data: MsgData) -> str:
    path = state_data.get("report:json_file_path")
    if path and os.path.exists(path):
        return path

    json_data = state_data.get("report:json_data")
    if not json_data:
        raise ValueError("Нет данных JSON")

    report_type = state_data.get("report:type", "revenue")
    period = state_data.get("report:period", "weekly")
    file_name = f"{report_type}_json_{period}.json"
    path = os.path.join(tempfile.gettempdir(), file_name)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    state_data["report:json_file_path"] = path
    await msg_data.state.update_data(state_data)

    return path

def cleanup_temp(paths: list[str]):
    for path in paths:
        if path and os.path.exists(path):
            os.remove(path)


async def send_report_stub(callback: CallbackQuery, msg_data: MsgData, format_type: str) -> None:
    state_data = await msg_data.state.get_data()
    report_format = format_type.upper()

    header = await make_header(msg_data)
    text = f"{header}\n\n📎 {report_format} отчёт прикреплён."

    try:
        json_file_path = state_data.get("report:json_file_path")

        # Автогенерация JSON, если путь не найден
        if not json_file_path or not os.path.exists(json_file_path):
            json_data = state_data.get("report:json_data")
            if not json_data:
                await callback.message.answer("Ошибка: нет данных для генерации JSON.")
                return

            type_data = state_data.get("report:type", "revenue")
            period = state_data.get("report:period", "weekly")
            file_name = f"{type_data}_json_{period}.json"

            json_file_path = os.path.join(tempfile.gettempdir(), file_name)
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)

            # Обновим state
            state_data["report:json_file_path"] = json_file_path
            await msg_data.state.update_data(state_data)

        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # Генерация PDF
        pdf_buffer = revenue_parameters_create_pdf_report(json_data)
        temp_pdf_path = os.path.join(tempfile.gettempdir(), "revenue_report.pdf")
        with open(temp_pdf_path, "wb") as f:
            f.write(pdf_buffer.read())

        await callback.message.answer_document(
            document=FSInputFile(temp_pdf_path),
            caption=text,
            reply_markup=report_keyboard
        )

    except Exception as e:
        await callback.message.answer(f"Ошибка при создании отчёта: {e}")
    finally:
        # Удаление временных файлов
        if "json_file_path" in locals() and os.path.exists(json_file_path):
            os.remove(json_file_path)
        if "temp_pdf_path" in locals() and os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)


@file_report_router.callback_query(F.data == "send_json_report")
async def handle_send_json_report(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    json_data = state_data.get("report:json_data")

    if not json_data:
        await callback.message.answer("Нет данных для JSON-отчёта.")
        return

    type_data = state_data.get("report:type", "revenue")
    format_type = "json"
    period = state_data.get("report:period", "weekly")
    file_name = f"{type_data}_{format_type}_{period}.json"

    file_path = os.path.join(tempfile.gettempdir(), file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    state_data["report:json_file_path"] = file_path
    await state.update_data(state_data)

    await callback.message.answer(f"Файл {file_name} успешно сохранён и готов для формирования отчёта.")
    await callback.answer()


# Создаем словарь для сопоставления имен функций с обработчиками
REPORT_HANDLERS = {
    # Revenue
    "generate_revenue_parameters_pdf": generate_revenue_pdf,
    "generate_revenue_parameters_excel": generate_revenue_excel,
    "generate_revenue_analysis_pdf": generate_revenue_analysis_pdf,
    "generate_revenue_analysis_excel": generate_revenue_analysis_excel,
    
    # Inventory
    "generate_inventory_parameters_pdf": generate_inventory_parameters_pdf,
    "generate_inventory_only_negative_pdf": generate_inventory_parameters_pdf,
    "generate_inventory_parameters_excel": generate_inventory_parameters_excel,
    "generate_inventory_only_negative_excel": generate_inventory_parameters_excel,
    
    # Write-off
    "generate_write_off_parameters_pdf": generate_write_off_parameters_pdf,
    "generate_write_off_parameters_excel": generate_write_off_parameters_excel,
    "generate_write_off_only_negative_pdf": generate_write_off_parameters_pdf,
    "generate_write_off_only_negative_excel": generate_write_off_parameters_excel,
    
    # Losses
    "losses_parameters_create_pdf_report": generate_losses_parameters_pdf,
    "losses_parameters_create_excel_report": generate_losses_parameters_excel,
    "losses_only_negative_create_pdf_report": generate_losses_only_negative_pdf,
    "losses_only_negative_create_excel_report": generate_losses_only_negative_excel,
    
    # Loss forecast
    "loss_forecast_parameters_create_pdf_report": generate_loss_forecast_parameters_pdf,
    "loss_forecast_parameters_create_excel_report": generate_loss_forecast_parameters_excel,
    "loss_forecast_only_negative_create_pdf_report": generate_loss_forecast_only_negative_pdf,
    "loss_forecast_only_negative_create_excel_report": generate_loss_forecast_only_negative_excel,
    
    # Food cost
    "food_cost_parameters_create_pdf_report": generate_food_cost_parameters_pdf,
    "food_cost_parameters_create_excel_report": generate_food_cost_parameters_excel,
    "food_cost_analysis_create_pdf_report": generate_food_cost_analysis_pdf,
    "food_cost_analysis_only_negative_create_pdf_report": generate_food_cost_analysis_pdf,
    "food_cost_analysis_create_excel_report": generate_food_cost_analysis_excel,
    "food_cost_analysis_only_negative_create_excel_report": generate_food_cost_analysis_excel,
    
    # Markup
    "markup_parameters_create_pdf_report": generate_markup_parameters_pdf,
    "markup_parameters_create_excel_report": generate_markup_parameters_excel,
    "markup_analysis_create_pdf_report": generate_markup_analysis_pdf,
    "markup_analysis_only_negative_create_pdf_report": generate_markup_analysis_pdf,
    "markup_analysis_create_excel_report": generate_markup_analysis_excel,
    "markup_analysis_only_negative_create_excel_report": generate_markup_analysis_excel,
    
    # Turnover
    "turnover_parameters_create_pdf_report": generate_turnover_parameters_pdf,
    "turnover_parameters_create_excel_report": generate_turnover_parameters_excel,
    "turnover_analysis_create_pdf_report": generate_turnover_analysis_pdf,
    "turnover_analysis_only_negative_create_pdf_report": generate_turnover_analysis_pdf,
    "turnover_analysis_create_excel_report": generate_turnover_analysis_excel,
    "turnover_analysis_only_negative_create_excel_report": generate_turnover_analysis_excel,
}


async def send_generated_report(callback: CallbackQuery, msg_data: MsgData) -> None:
    state_data = await msg_data.state.get_data()
    report_type = state_data.get("report:type")
    format_type = state_data.get("report:format_type")
    file_type = state_data.get("report:delivery_format")

    func_name = REPORT_GENERATORS.get((report_type, format_type, file_type))
    if not func_name:
        await callback.message.answer("Формат или тип отчёта не поддерживается.")
        return

    handler = REPORT_HANDLERS.get(func_name)
    if handler:
        await handler(callback, msg_data)
    else:
        await callback.message.answer("Формат или тип отчёта не поддерживается.")


