from fastapi import APIRouter, HTTPException, Request

from app.config import TELEGRAM_WEBHOOK_SECRET
from app.services.telegram_service import TelegramService

router = APIRouter()
service = TelegramService()


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request) -> dict:
    if TELEGRAM_WEBHOOK_SECRET:
        secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret_header != TELEGRAM_WEBHOOK_SECRET:
            raise HTTPException(status_code=403, detail="Invalid webhook secret")
    update = await request.json()
    service.handle_update(update)
    return {"ok": True}


def send_scheduled_summary() -> int:
    return service.send_scheduled_summary()


def handle_update(update: dict) -> None:
    service.handle_update(update)


def send_bot_message(chat_id: str, text: str) -> None:
    service.send_bot_message(chat_id, text)


def help_message() -> str:
    return service.help_message()
