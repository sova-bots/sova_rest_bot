import sqlite3
import config as cf
from src.log import logger


class UserTokensDB:
    def __init__(self, path):
        # Устанавливаем соединение с базой данных
        self.conn = sqlite3.connect(path)
        self.cursor = self.conn.cursor()
        self.path = path

    def insert_user(self, tgid: str, token: str) -> None:
        self.cursor.execute('''
        INSERT INTO Users (tgid, token) VALUES (?, ?)
        ''', (tgid, token,))
        self.conn.commit()

    def get_token(self, tgid: str) -> str | None:
        self.cursor.execute('''
        SELECT * FROM Users WHERE tgid == ?
        ''', (tgid,))
        result = self.cursor.fetchone()
        if result is None:
            return None
        return result[1]

    def has_tgid(self, tgid: str) -> bool:
        return self.get_token(tgid) is not None

    def delete_user(self, tgid: str) -> bool:
        self.cursor.execute('''
        DELETE FROM Users WHERE tgid == ?
        ''', (tgid,))
        self.conn.commit()

    def create_table(self):
        # Создаем таблицу Users
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
        tgid TEXT PRIMARY KEY,
        token TEXT NOT NULL
        )
        ''')
        # Сохраняем изменения и закрываем соединение
        self.conn.commit()

    def close(self):
        self.conn.close()


def create_database(path: str) -> UserTokensDB:
    try:
        db = UserTokensDB(path)
        db.create_table()
        return db
    except sqlite3.OperationalError:
        logger.msg("ERROR", f"Please create directory for the database: {path}")
        raise BaseException(f"Please create directory for the database: {path}")


user_tokens_db = create_database(cf.USER_TOKENS_DB_PATH)


def get_user_tokens_db() -> UserTokensDB | None:
    global user_tokens_db
    return user_tokens_db
