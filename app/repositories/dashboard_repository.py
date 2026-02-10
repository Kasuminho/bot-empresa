from app.db import get_connection
from app.models.dashboard import DashboardData


class DashboardRepository:
    def fetch_dashboard(self) -> DashboardData:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE 0 END) AS total_credit,
                    SUM(CASE WHEN transaction_type = 'debit' THEN amount ELSE 0 END) AS total_debit,
                    COUNT(*) AS total_transactions
                FROM bank_transactions
                """
            )
            stats = cursor.fetchone()
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM bank_transactions bt
                LEFT JOIN payments p ON p.bank_transaction_id = bt.id
                LEFT JOIN bank_reconciliations br ON br.bank_transaction_id = bt.id
                WHERE p.id IS NOT NULL OR br.id IS NOT NULL
                """
            )
            reconciled_count = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM loads WHERE status != 'paid'")
            pending_loads = cursor.fetchone()
            cursor.execute(
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
            )
            bank_transactions = cursor.fetchall()
            cursor.execute(
                """
                SELECT l.*, d.name AS driver_name, t.plate AS truck_plate
                FROM loads l
                LEFT JOIN drivers d ON d.id = l.driver_id
                LEFT JOIN trucks t ON t.id = l.truck_id
                WHERE l.status != 'paid'
                ORDER BY l.load_date DESC
                """
            )
            loads = cursor.fetchall()
        connection.close()
        return DashboardData(
            bank_transactions=bank_transactions,
            loads=loads,
            stats=stats,
            reconciled_count=reconciled_count,
            pending_loads=pending_loads,
        )

    def reconcile(
        self,
        bank_transaction_id: int,
        reconciliation_type: str,
        notes: str | None,
        load_ids: list[int] | None,
    ) -> None:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT amount FROM bank_transactions WHERE id = %s",
                (bank_transaction_id,),
            )
            txn = cursor.fetchone()
            total_amount = txn["amount"] if txn else 0.0
            if reconciliation_type == "loads":
                cursor.execute(
                    "INSERT INTO payments (bank_transaction_id, total_amount) VALUES (%s, %s)",
                    (bank_transaction_id, total_amount),
                )
                cursor.execute("SELECT LASTVAL() AS id")
                payment_id = cursor.fetchone()["id"]
                selected_loads = load_ids or []
                if selected_loads:
                    cursor.executemany(
                        "INSERT INTO payment_loads (payment_id, load_id) VALUES (%s, %s)",
                        [(payment_id, load_id) for load_id in selected_loads],
                    )
                    cursor.executemany(
                        "UPDATE loads SET status = 'paid' WHERE id = %s",
                        [(load_id,) for load_id in selected_loads],
                    )
            cursor.execute(
                """
                INSERT INTO bank_reconciliations (bank_transaction_id, reconciliation_type, notes)
                VALUES (%s, %s, %s)
                """,
                (bank_transaction_id, reconciliation_type, notes),
            )
        connection.commit()
        connection.close()
