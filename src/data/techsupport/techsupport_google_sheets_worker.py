from gspread.cell import Cell

import config as cf
from src.data.google_sheets_worker import GoogleSheetsWorker


class TechSupportMessage:
    def __init__(self, _id: str, question: str, answer: str, photo_id: str, client_id: str, admin_username: str):
        self.id = _id
        self.question = question
        self.answer = answer
        self.photo_id = photo_id
        self.client_id = client_id
        self.admin_username = admin_username

    def __init__(self, values: list):
        self.id = values[Columns.id_]
        self.question = values[Columns.question]
        self.answer = values[Columns.answer]
        self.photo_id = values[Columns.photo_id]
        self.client_id = values[Columns.client_id]
        self.admin_username = values[Columns.admin_id]


class TSList:
    def __init__(self, values: list[TechSupportMessage]):
        self.values = values

    def filter(self, admin_username: int | None = None):
        result = self.values.copy()
        for v in result.copy():
            if admin_username is not None and v.admin_username != admin_username:
                result.remove(v)
        return result


class Columns:
    id_: int = 0
    question: int = 1
    answer: int = 2
    photo_id: int = 3
    client_id: int = 4
    admin_id: int = 5


class Const:
    NO_DATA = 'none'


class TechSupportGoogleSheetsWorker(GoogleSheetsWorker):
    def __init__(self, spreadsheet_url: str, worksheet_title: str | None = None):
        super().__init__(spreadsheet_url, worksheet_title)

    def find_top_empty_row(self, col: int) -> int:
        return len(self.ws.col_values(col+1))

    def write_techsupport(self, question: str, photo_id: str, client_id: int) -> None:
        row = self.find_top_empty_row(Columns.question)

        self.ws.update_cells([
            Cell(
                row=row + 1,
                col=Columns.id_ + 1,
                value=str(row)
            ),
            Cell(
                row=row + 1,
                col=Columns.question + 1,
                value=question
            ),
            Cell(
                row=row + 1,
                col=Columns.photo_id + 1,
                value=photo_id
            ),
            Cell(
                row=row + 1,
                col=Columns.client_id + 1,
                value=str(client_id)
            )
        ])

    def get_admin_dict(self) -> dict[str, str]:
        ws = self.get_worksheet("админы")
        values = ws.get_all_values()[1:]
        usernames = [pair[0] for pair in values]
        user_ids = [pair[1] for pair in values]
        return dict(zip(user_ids, usernames))

    def get_admin_user_ids(self) -> list[int]:
        ws = self.get_worksheet("админы")
        values = ws.col_values(col=2)
        return [int(v) for v in values[1:]]

    def get_admin_usernames(self) -> list[int]:
        ws = self.get_worksheet("админы")
        values = ws.col_values(col=1)
        return [v for v in values[1:]]

    def write_admin_user_id(self, user_id: int, row: int) -> None:
        ws = self.get_worksheet("админы")
        ws.update_cell(col=2, row=row, value=str(user_id))

    def get_techsupport_by_admin_id(self, admin_id: int | None = None) -> list[TechSupportMessage]:
        values = self.ws.get_all_values()[1:]

        admins = self.get_admin_dict()

        tslist = TSList(values=[
            TechSupportMessage(row) for row in values
        ])

        return tslist.filter(
            admin_username=admins[str(admin_id)] if admin_id is not None else None
        )

    def get_techsupport_by_id(self, ts_id: str) -> TechSupportMessage:
        row = int(ts_id)
        values = self.ws.row_values(
            row=row + 1
        )
        return TechSupportMessage(values)

    def find_ts_row(self, _id: str) -> int | None:
        cell = self.ws.find(
            query=_id,
            in_column=Columns.id_
        )

        if cell is None:
            return None

        return cell.row

    def write_answer(self, _id: str, answer: str) -> bool:
        row = int(_id)

        self.ws.update_cell(
            row=row + 1,
            col=Columns.answer + 1,
            value=answer
        )

        return True

    def get_client_id(self, _id: str) -> int | None:
        row = int(_id)

        value = self.ws.cell(
            row=row + 1,
            col=Columns.client_id + 1
        )

        if value is None:
            return None

        return value.value


techsupport_gsworker = TechSupportGoogleSheetsWorker(cf.TECHSUPPORT_SPREADSHEET_URL)
