import os

from dotenv import load_dotenv

load_dotenv()


def get_env(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


DB_PATH = get_env("BOT_EMPRESA_DB_PATH", "/workspace/bot-empresa/data/bot_empresa.db")
TELEGRAM_TOKEN = get_env("BOT_TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = get_env("BOT_TELEGRAM_CHAT_ID")
