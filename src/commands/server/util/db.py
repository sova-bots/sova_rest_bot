import os
import sqlite3

import sqlite3


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

    def get_token(self, tgid: str) -> str:
        self.cursor.execute('''
        SELECT * FROM Users WHERE tgid == ?
        ''', (tgid,))
        return self.cursor.fetchone()[1]

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


user_tokens_db = None


def init_user_tokens_db(path):
    global user_tokens_db
    user_tokens_db = UserTokensDB(path)


def get_user_tokens_db() -> UserTokensDB | None:
    global user_tokens_db
    return user_tokens_db


if __name__ == '__main__':
    init_user_tokens_db("../../../../resources/db/user_tokens.db")
    get_user_tokens_db().create_table()

