import config as cf
from ...commands.registration.register.registration_form import RegistrationForm
from ...data.google_sheets_worker import GoogleSheetsWorker


class MessageColumn:
    DAY: int = 5
    WEEK: int = 6
    MONTH: int = 7


class indexes:
    password = 2
    login = 1
    subdomain = 0


class NotificationGoogleSheetsWorker(GoogleSheetsWorker):
    def __init__(self, spreadsheet_url: str, worksheet_title: str | None = None):
        super().__init__(spreadsheet_url, worksheet_title)

    def get_messages(self, message_col: int, id_col: int = 4, start_row: int = 4):
        values = self.ws.get_all_values()

        for row in values[start_row:]:
            try:
                user_id = row[id_col]
                message = row[message_col]
            except IndexError:
                continue

            if user_id and message:
                yield user_id, message

    def contains_id(self, user_id: int) -> bool:
        cell = self.ws.find(str(user_id))
        if cell is None:
            return False
        return True

    def register_id(self, row: int, user_id: int) -> bool:
        cell = self.ws.find(str(user_id))

        if cell is not None:
            return False

        col: int = 5
        self.ws.update_cell(row, col, value=user_id)
        return True

    def remove_id(self, user_id: int) -> bool:
        cell = self.ws.find(str(user_id))

        if cell is None:
            return False

        self.ws.update_cell(cell.row, cell.col, '')
        return True

    def get_form_row(self, form: RegistrationForm) -> int | None:
        cell = self.ws.find(form.login)

        if cell is None:
            return None

        row = cell.row

        values = self.ws.row_values(row)

        if form.subdomain != values[indexes.subdomain]:
            return None
        if form.password != values[indexes.password]:
            return None

        return row


notification_gsworker = NotificationGoogleSheetsWorker(cf.NOTIFICATION_SPREADSHEET_URL)
