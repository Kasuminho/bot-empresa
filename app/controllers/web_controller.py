from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.importers import import_loads
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


@router.post("/api/loads/import-csv")
async def import_loads_csv(
    file: UploadFile = File(...),
    sheet_owner: str | None = Form(None),
) -> JSONResponse:
    suffix = Path(file.filename or "loads.csv").suffix or ".csv"
    with NamedTemporaryFile(mode="wb", suffix=suffix, delete=False) as temp_file:
        temp_file.write(await file.read())
        temp_path = Path(temp_file.name)

    try:
        imported_count = import_loads(temp_path, sheet_owner=sheet_owner)
    finally:
        temp_path.unlink(missing_ok=True)

    return JSONResponse(
        {
            "ok": True,
            "imported_count": imported_count,
            "sheet_owner": sheet_owner,
        }
    )
