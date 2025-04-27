from asyncio.log import logger

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
        logger.info(f"Отправляем на проверку в Google Sheets: login={form.login}, password={form.password}")

        # Поиск логина в таблице
        cell = self.ws.find(form.login.strip().lower())

        if cell is None:
            logger.info(f"Логин {form.login} не найден в Google Sheets")
            return None

        row = cell.row
        values = self.ws.row_values(row)

        # Проверяем, что длина values достаточна
        if len(values) <= max(indexes.password, indexes.subdomain):
            logger.error(f"Некорректная строка данных в Google Sheets: {values}")
            return None

        # Проверяем соответствие пароля
        if form.password != values[indexes.password]:
            logger.info(f"Неверный пароль для логина {form.login}")
            return None

        # Если subdomain важен — оставляем, если нет — убираем проверку
        if hasattr(form, 'subdomain') and form.subdomain != values[indexes.subdomain]:
            logger.info(f"Несоответствие subdomain у {form.login}")
            return None

        logger.info(f"Пользователь {form.login} найден в строке {row}")
        return row

    def check_user_exists(self, user_id: int) -> bool:
        return self.contains_id(user_id)

    def get_token_by_user_id(self, user_id: int) -> str | None:
        cell = self.ws.find(str(user_id))  # Ищем ячейку с Telegram ID
        if cell is None:
            return None  # Пользователь не найден

        # Получаем токен из той же строки, но из колонки с токеном
        token = self.ws.cell(cell.row, 3).value  # Предположим, токен в колонке 3
        return token


notification_gsworker = NotificationGoogleSheetsWorker(cf.NOTIFICATION_SPREADSHEET_URL)
