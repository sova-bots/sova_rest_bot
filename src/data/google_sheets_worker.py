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