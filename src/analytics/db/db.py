import sqlite3
import config as cf
from asyncpg import create_pool, PostgresError

import logging
import asyncpg

from src.mailing.notifications.check_time import DB_CONFIG

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)



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
        logger.error(f"Please create directory for the database: {path}")  # Логирование ошибки
        raise BaseException(f"Please create directory for the database: {path}")


user_tokens_db = create_database(cf.USER_TOKENS_DB_PATH)


def get_user_tokens_db() -> UserTokensDB | None:
    global user_tokens_db
    return user_tokens_db


async def get_report_hint_text(tg_id: int, report_type: str, report_format: str) -> dict | None:
    """
    Получение текста подсказки и ссылки для отчета из БД.
    Приоритет: точное совпадение -> универсальный формат ('all_format').
    """
    try:
        conn = await asyncpg.connect(**DB_CONFIG)

        query = """
        SELECT rdl.description, ul.link
        FROM user_links ul
        LEFT JOIN report_data_link rdl
            ON rdl.report_type = ul.report_type
           AND (
                rdl.report_format = ul.report_format
             OR rdl.report_format = 'all_format'
            )
        WHERE ul.tg_id = $1
          AND ul.report_type = $2
          AND ul.report_format = $3
        ORDER BY 
            CASE WHEN rdl.report_format = ul.report_format THEN 1
                 WHEN rdl.report_format = 'all_format' THEN 2
                 ELSE 3
            END
        LIMIT 1;
        """

        logging.info(f"[get_report_hint_text] Поиск по: tg_id={tg_id}, report_type={report_type}, report_format={report_format}")
        row = await conn.fetchrow(query, tg_id, report_type, report_format)

        if row:
            return {"description": row["description"], "url": row["link"]}
        else:
            logging.warning(f"[get_report_hint_text] Ничего не найдено по tg_id={tg_id}, report_type={report_type}, format={report_format}")
            return None

    except PostgresError as e:
        logging.error(f"[get_report_hint_text] Ошибка БД: {e}")
        return None
    except Exception as e:
        logging.error(f"[get_report_hint_text] Неожиданная ошибка: {e}")
        return None
    finally:
        if 'conn' in locals():
            await conn.close()
