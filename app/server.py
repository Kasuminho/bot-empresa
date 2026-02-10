import asyncio

from fastapi import FastAPI

from app.config import SUMMARY_SCHEDULE_ENABLED, SUMMARY_SCHEDULE_INTERVAL_MINUTES
from app.controllers.telegram_controller import router as telegram_router
from app.controllers.telegram_controller import send_scheduled_summary
from app.controllers.web_controller import router as web_router

app = FastAPI()
app.include_router(web_router)
app.include_router(telegram_router)


@app.on_event("startup")
async def startup_jobs() -> None:
    if not SUMMARY_SCHEDULE_ENABLED:
        return

    async def _summary_loop() -> None:
        while True:
            try:
                send_scheduled_summary()
            except Exception:
                pass
            await asyncio.sleep(max(1, SUMMARY_SCHEDULE_INTERVAL_MINUTES) * 60)

    asyncio.create_task(_summary_loop())
