from app.db import get_connection


class FinanceRepository:
    def get_load_for_dispatcher_fee(self, load_external_id: str, connection=None):
        should_close = False
        if connection is None:
            connection = get_connection()
            should_close = True
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT l.id, l.external_id, l.load_date, l.amount_gross, l.recife_fee_percent,
                       t.owner_id
                FROM loads l
                LEFT JOIN trucks t ON t.id = l.truck_id
                WHERE l.external_id = %s
                """,
                (load_external_id,),
            )
            row = cursor.fetchone()
        if should_close:
            connection.close()
        return row

    def dispatcher_fee_exists(self, description: str, amount: float, expense_date, connection=None) -> bool:
        should_close = False
        if connection is None:
            connection = get_connection()
            should_close = True
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM expenses
                WHERE description = %s AND amount = %s AND expense_date = %s
                """,
                (description, amount, expense_date),
            )
            row = cursor.fetchone()
        if should_close:
            connection.close()
        return bool(row)

    def insert_dispatcher_fee_expense(self, owner_id, expense_date, fee_amount: float, description: str, connection=None) -> None:
        should_close = False
        if connection is None:
            connection = get_connection()
            should_close = True
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO expenses (
                    owner_id,
                    truck_id,
                    bank_account_id,
                    expense_date,
                    amount,
                    description,
                    category,
                    cost_center
                )
                VALUES (%s, %s, NULL, %s, %s, %s, 'dispatcher', 'Dispatcher fee')
                """,
                (owner_id, None, expense_date, fee_amount, description),
            )
        connection.commit()
        if should_close:
            connection.close()

    def get_week_loads(self, week_reference: str):
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    l.id,
                    l.amount_gross,
                    l.slv_fee_percent,
                    l.recife_fee_percent,
                    l.week_reference,
                    l.driver_id,
                    t.owner_id
                FROM loads l
                LEFT JOIN trucks t ON t.id = l.truck_id
                WHERE l.week_reference = %s
                """,
                (week_reference,),
            )
            rows = cursor.fetchall()
        connection.close()
        return rows

    def ledger_entry_exists(self, owner_id, driver_id, description: str) -> bool:
        connection = get_connection()
        with connection.cursor() as cursor:
            if driver_id is not None:
                cursor.execute(
                    """
                    SELECT id FROM ledger_entries
                    WHERE driver_id = %s AND entry_type = 'weekly_commission' AND description = %s
                    """,
                    (driver_id, description),
                )
            else:
                cursor.execute(
                    """
                    SELECT id FROM ledger_entries
                    WHERE owner_id = %s AND entry_type = 'weekly_commission' AND description = %s
                    """,
                    (owner_id, description),
                )
            row = cursor.fetchone()
        connection.close()
        return bool(row)

    def insert_ledger_entry(self, owner_id, driver_id, entry_date: str, amount: float, description: str) -> None:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ledger_entries (
                    owner_id,
                    driver_id,
                    entry_date,
                    entry_type,
                    amount,
                    description
                )
                VALUES (%s, %s, %s, 'weekly_commission', %s, %s)
                """,
                (owner_id, driver_id, entry_date, amount, description),
            )
        connection.commit()
        connection.close()

    def get_ledger_rows(self, owner_external_id: str | None, driver_external_id: str | None, limit: int):
        connection = get_connection()
        params: list = []
        where_clause = ""
        if owner_external_id:
            where_clause = "WHERE owner_id = (SELECT id FROM owners WHERE external_id = %s)"
            params.append(owner_external_id)
        elif driver_external_id:
            where_clause = "WHERE driver_id = (SELECT id FROM drivers WHERE external_id = %s)"
            params.append(driver_external_id)
        query = f"""
            SELECT entry_date, entry_type, amount, description
            FROM ledger_entries
            {where_clause}
            ORDER BY entry_date DESC, id DESC
            LIMIT %s
        """
        params.append(limit)
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        connection.close()
        return rows

    def get_summary_stats(self):
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE 0 END) AS total_credit,
                    SUM(CASE WHEN transaction_type = 'debit' THEN amount ELSE 0 END) AS total_debit
                FROM bank_transactions
                """
            )
            stats = cursor.fetchone()
            cursor.execute("SELECT SUM(amount) AS total_expenses FROM expenses")
            expenses = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) AS pending_count FROM loads WHERE status != 'paid'")
            pending = cursor.fetchone()
        connection.close()
        return stats, expenses, pending

    def get_transaction_by_external_id(self, transaction_external_id: str):
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, external_id, txn_date, amount
                FROM bank_transactions
                WHERE external_id = %s
                """,
                (transaction_external_id,),
            )
            row = cursor.fetchone()
        connection.close()
        return row

    def list_open_load_candidates(self, amount: float, txn_date, limit: int):
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    l.external_id,
                    l.load_date,
                    l.amount_gross,
                    ABS(l.amount_gross - %s) AS amount_gap,
                    ABS(l.load_date - %s) AS day_gap
                FROM loads l
                WHERE l.status != 'paid'
                ORDER BY amount_gap ASC, day_gap ASC
                LIMIT %s
                """,
                (amount, txn_date, limit),
            )
            rows = cursor.fetchall()
        connection.close()
        return rows

    def get_open_loads_aggregate(self, owner_external_id: str | None, driver_external_id: str | None):
        connection = get_connection()
        where_clause = "WHERE l.status != 'paid'"
        params: list[str] = []
        if owner_external_id:
            where_clause += " AND t.owner_id = (SELECT id FROM owners WHERE external_id = %s)"
            params.append(owner_external_id)
        elif driver_external_id:
            where_clause += " AND l.driver_id = (SELECT id FROM drivers WHERE external_id = %s)"
            params.append(driver_external_id)
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    COUNT(*) AS open_count,
                    SUM(l.amount_gross) AS gross_total,
                    SUM(l.amount_gross * (l.slv_fee_percent / 100.0)) AS slv_fee_total,
                    SUM(l.amount_gross * (l.recife_fee_percent / 100.0)) AS recife_fee_total
                FROM loads l
                LEFT JOIN trucks t ON t.id = l.truck_id
                {where_clause}
                """,
                params,
            )
            row = cursor.fetchone()
        connection.close()
        return row
