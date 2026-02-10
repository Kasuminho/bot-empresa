from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.web_service import WebService

router = APIRouter()
templates = Jinja2Templates(directory="/workspace/bot-empresa/app/templates")
service = WebService()


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    data = service.fetch_dashboard()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "bank_transactions": data.bank_transactions,
            "loads": data.loads,
            "stats": data.stats,
            "reconciled_count": data.reconciled_count,
            "pending_loads": data.pending_loads,
        },
    )


@router.post("/reconcile")
def reconcile(
    bank_transaction_id: int = Form(...),
    reconciliation_type: str = Form(...),
    notes: str | None = Form(None),
    load_ids: list[int] | None = Form(None),
):
    service.reconcile(bank_transaction_id, reconciliation_type, notes, load_ids)
    return RedirectResponse("/", status_code=303)
