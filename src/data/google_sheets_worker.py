import gspread
from gspread import Client, Spreadsheet, Worksheet

from types import GeneratorType

from src.commands.register.registration_form import RegistrationForm

import config as cf

gclient: Client = gspread.service_account(cf.KEY_PATH)


class GoogleSheetsWorker:
    gc: Client
    sh: Spreadsheet
    ws: Worksheet

    def __init__(self, spreadsheet_url: str, worksheet_title: str | None = None) -> None:
        self.gc = gclient
        self.sh = self.gc.open_by_url(spreadsheet_url)
        self.ws = self.sh.worksheet(worksheet_title) if worksheet_title is not None else self.sh.sheet1

    def get_worksheet(self, title: str) -> Worksheet:
        return self.sh.worksheet(title)

    def get_buttons(self, sheet_title: str) -> dict[int, dict]:
        ws = self.get_worksheet(sheet_title)
        rows = ws.get_all_values()[1:]
        options = {}
        index = 0

        for row in rows:
            if len(row) < 3:
                continue

            btn_type, main_option, sub_option = row[:3]

            if btn_type == "option":
                options[index] = {
                    "text": main_option,
                    "response": sub_option,
                    "sub_options": {}
                }
                index += 1

            elif btn_type == "sub_option":
                parent_index = next((i for i, opt in options.items() if opt["text"] == main_option), None)
                if parent_index is not None:
                    options[parent_index]["sub_options"][index] = sub_option
                    index += 1

        return options