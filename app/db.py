import sqlite3
from pathlib import Path

from app.config import DB_PATH


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else Path(DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: Path | str | None = None) -> None:
    connection = get_connection(db_path)
    schema_path = Path(__file__).with_name("schema.sql")
    with schema_path.open("r", encoding="utf-8") as schema_file:
        connection.executescript(schema_file.read())
    connection.commit()
    connection.close()
