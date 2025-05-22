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

    table_data = [["Магазин", "Прогноз", "Изменение цены (1 месяц)", "Изменение цены (2 месяца)"]]

    # Sort the stores based on 'forecast' in descending order
    sorted_data = sorted(data["data"], key=lambda store: store.get("forecast", 0), reverse=True)

    for store in sorted_data:
        forecast = store.get("forecast", "-")

        # Get the first non-null price differences for -1 month and -2 months
        diff_price_1 = get_first_non_null(store.get("diff_price"), store.get("diff_price2"), store.get("diff_price3"), store.get("diff_price4"))
        diff_price_2 = get_first_non_null(store.get("diff_price3"), store.get("diff_price4"), store.get("diff_price2"), store.get("diff_price"))

        # Skip the store if both price differences are null
        if diff_price_1 == "-" and diff_price_2 == "-":
            continue  # Do not add this store to the table

        # Round the price differences to 2 decimal places if they are numbers
        if isinstance(diff_price_1, (int, float)):
            diff_price_1 = round(diff_price_1, 2)
        if isinstance(diff_price_2, (int, float)):
            diff_price_2 = round(diff_price_2, 2)

        # Add the row with the store's label, forecast, and price differences
        table_data.append([
            store["label"],
            f"{forecast:,.2f}" if isinstance(forecast, (int, float)) else forecast,
            f"{diff_price_1:,.2f}" if isinstance(diff_price_1, (int, float)) else "-",
            f"{diff_price_2:,.2f}" if isinstance(diff_price_2, (int, float)) else "-"
        ])

    table = Table(table_data, colWidths=[2.2 * inch, 1.6 * inch, 1.6 * inch, 1.6 * inch])
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

    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer


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

    # Table header with 5 columns: Store, Forecast, First Price Change, Price Change 1 Month, Price Change 2 Months
    table_data = [["Магазин", "Прогноз", "Первое изменение цены", "Изменение цены (1 месяц)", "Изменение цены (2 месяца)"]]

    # Sort the stores based on 'forecast' in descending order
    sorted_data = sorted(data["data"], key=lambda store: store.get("forecast", 0), reverse=True)

    for store in sorted_data:
        forecast = store.get("forecast", "-")

        # Get the first non-null price differences for -1 month and -2 months
        diff_price_1 = get_first_non_null(store.get("diff_price"), store.get("diff_price2"), store.get("diff_price3"), store.get("diff_price4"))
        diff_price_2 = get_first_non_null(store.get("diff_price3"), store.get("diff_price4"), store.get("diff_price2"), store.get("diff_price"))

        # Get the price changes for 1 month and 2 months
        diff_price_2 = store.get("diff_price", "-")
        diff_price_3 = store.get("diff_price3", "-")

        # Calculate price difference between 1 month and 2 months
        if isinstance(diff_price_2, (int, float)) and isinstance(diff_price_3, (int, float)):
            diff_price_1_month = round(diff_price_3 - diff_price_2, 2)
        else:
            diff_price_1_month = "-"

        # Calculate price difference between 2 months and 3 months
        diff_price_4 = store.get("diff_price4", "-")
        if isinstance(diff_price_3, (int, float)) and isinstance(diff_price_4, (int, float)):
            diff_price_2_month = round(diff_price_4 - diff_price_3, 2)
        else:
            diff_price_2_month = "-"

        # Skip the store if no valid price change is found
        if diff_price_1 == "-" and diff_price_1_month == "-" and diff_price_2_month == "-":
            continue  # Do not add this store to the table

        # Add the row with the store's name, forecast, and price differences
        table_data.append([
            store["label"],
            f"{forecast:,.2f}" if isinstance(forecast, (int, float)) else forecast,
            f"{diff_price_1:,.2f}" if isinstance(diff_price_1, (int, float)) else "-",
            f"{diff_price_1_month:,.2f}" if isinstance(diff_price_1_month, (int, float)) else "-",
            f"{diff_price_2_month:,.2f}" if isinstance(diff_price_2_month, (int, float)) else "-"
        ])

    table = Table(table_data, colWidths=[2.2 * inch, 1.6 * inch, 1.6 * inch, 1.6 * inch, 1.6 * inch])
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

    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer