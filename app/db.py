from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import DB_PATH


def get_connection(db_url: str | None = None):
    url = db_url or DB_PATH
    connection = psycopg2.connect(url, cursor_factory=RealDictCursor)
    return connection


def init_db(db_url: str | None = None) -> None:
    connection = get_connection(db_url)
    schema_path = Path(__file__).with_name("schema.sql")
    with schema_path.open("r", encoding="utf-8") as schema_file:
        schema_sql = schema_file.read()
    with connection.cursor() as cursor:
        for statement in schema_sql.split(";"):
            stmt = statement.strip()
            if stmt:
                cursor.execute(stmt)
    connection.commit()
    connection.close()
