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

    def get_buttons(self, sheet_title: str) -> dict[str, dict[str, dict]]:

        ws = self.get_worksheet(sheet_title)
        rows = ws.get_all_values()[1:]
        options = {}

        for row in rows:
            btn_type, main_option, sub_option = row

            if btn_type == "option":
                options[main_option] = {
                    "text": main_option,
                    "response": sub_option,
                    "sub_options": {}
                }
            elif btn_type == "sub_option" and main_option in options:
                options[main_option]["sub_options"][sub_option] = f"{sub_option} для {main_option}"

        return options