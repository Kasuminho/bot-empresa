import os
from pathlib import Path


def _load_dotenv() -> None:
    env_path = Path(".env")
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv()


def get_env(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


DB_PATH = get_env("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bot_empresa")
TELEGRAM_TOKEN = get_env("BOT_TELEGRAM_TOKEN")
TELEGRAM_WEBHOOK_SECRET = get_env("BOT_TELEGRAM_WEBHOOK_SECRET")

TELEGRAM_ADMIN_CHAT_IDS = [
    item.strip()
    for item in (get_env("BOT_TELEGRAM_ADMIN_CHAT_IDS", "") or "").split(",")
    if item.strip()
]
SUMMARY_SCHEDULE_ENABLED = (get_env("BOT_SUMMARY_SCHEDULE_ENABLED", "0") or "0") == "1"
SUMMARY_SCHEDULE_INTERVAL_MINUTES = int(
    get_env("BOT_SUMMARY_SCHEDULE_INTERVAL_MINUTES", "60") or "60"
)
