from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import get_connection

app = FastAPI()
templates = Jinja2Templates(directory="/workspace/bot-empresa/app/templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    connection = get_connection()
    stats = connection.execute(
        """
        SELECT
            SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE 0 END) AS total_credit,
            SUM(CASE WHEN transaction_type = 'debit' THEN amount ELSE 0 END) AS total_debit,
            COUNT(*) AS total_transactions
        FROM bank_transactions
        """
    ).fetchone()
    reconciled_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM bank_transactions bt
        LEFT JOIN payments p ON p.bank_transaction_id = bt.id
        LEFT JOIN bank_reconciliations br ON br.bank_transaction_id = bt.id
        WHERE p.id IS NOT NULL OR br.id IS NOT NULL
        """
    ).fetchone()
    pending_loads = connection.execute(
        "SELECT COUNT(*) FROM loads WHERE status != 'paid'"
    ).fetchone()
    bank_transactions = connection.execute(
        """
        SELECT
            bt.*,
            p.id AS payment_id,
            br.reconciliation_type,
            br.notes,
            ba.label AS account_label
        FROM bank_transactions bt
        LEFT JOIN payments p ON p.bank_transaction_id = bt.id
        LEFT JOIN bank_reconciliations br ON br.bank_transaction_id = bt.id
        LEFT JOIN bank_accounts ba ON ba.id = bt.account_id
        ORDER BY bt.txn_date DESC
        """
    ).fetchall()
    loads = connection.execute(
        """
        SELECT l.*, d.name AS driver_name, t.plate AS truck_plate
        FROM loads l
        LEFT JOIN drivers d ON d.id = l.driver_id
        LEFT JOIN trucks t ON t.id = l.truck_id
        WHERE l.status != 'paid'
        ORDER BY l.load_date DESC
        """
    ).fetchall()
    connection.close()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "bank_transactions": bank_transactions,
            "loads": loads,
            "stats": stats,
            "reconciled_count": reconciled_count,
            "pending_loads": pending_loads,
        },
    )


@app.post("/reconcile")
def reconcile(
    bank_transaction_id: int = Form(...),
    reconciliation_type: str = Form(...),
    notes: str | None = Form(None),
    load_ids: list[int] | None = Form(None),
):
    connection = get_connection()
    cursor = connection.cursor()
    txn = cursor.execute(
        "SELECT amount FROM bank_transactions WHERE id = ?",
        (bank_transaction_id,),
    ).fetchone()
    total_amount = txn[0] if txn else 0.0
    if reconciliation_type == "loads":
        cursor.execute(
            "INSERT INTO payments (bank_transaction_id, total_amount) VALUES (?, ?)",
            (bank_transaction_id, total_amount),
        )
        payment_id = cursor.lastrowid
        selected_loads = load_ids or []
        if selected_loads:
            cursor.executemany(
                "INSERT INTO payment_loads (payment_id, load_id) VALUES (?, ?)",
                [(payment_id, load_id) for load_id in selected_loads],
            )
            cursor.executemany(
                "UPDATE loads SET status = 'paid' WHERE id = ?",
                [(load_id,) for load_id in selected_loads],
            )
    cursor.execute(
        """
        INSERT INTO bank_reconciliations (bank_transaction_id, reconciliation_type, notes)
        VALUES (?, ?, ?)
        """,
        (bank_transaction_id, reconciliation_type, notes),
    )
    connection.commit()
    connection.close()
    return RedirectResponse("/", status_code=303)
