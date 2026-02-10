from datetime import date

from app.repositories.finance_repository import FinanceRepository


class FinanceService:
    def __init__(self, repository: FinanceRepository | None = None) -> None:
        self.repository = repository or FinanceRepository()

    @staticmethod
    def _calculate_fee(amount: float, percent: float) -> float:
        return round(amount * (percent / 100.0), 2)

    def ensure_dispatcher_fee_expense(self, load_external_id: str, connection=None) -> None:
        if not load_external_id:
            return
        load = self.repository.get_load_for_dispatcher_fee(load_external_id, connection=connection)
        if not load:
            return
        fee_percent = load["recife_fee_percent"] or 0.0
        if fee_percent <= 0:
            return
        fee_amount = self._calculate_fee(load["amount_gross"], fee_percent)
        description = f"Dispatcher fee load {load['external_id']}"
        exists = self.repository.dispatcher_fee_exists(
            description,
            fee_amount,
            load["load_date"],
            connection=connection,
        )
        if exists:
            return
        self.repository.insert_dispatcher_fee_expense(
            load["owner_id"],
            load["load_date"],
            fee_amount,
            description,
            connection=connection,
        )

    def close_week(self, week_reference: str) -> dict[str, float]:
        loads = self.repository.get_week_loads(week_reference)
        driver_totals: dict[int, float] = {}
        owner_totals: dict[int, float] = {}
        for load in loads:
            amount = load["amount_gross"]
            slv_fee = self._calculate_fee(amount, load["slv_fee_percent"] or 0.0)
            recife_fee = self._calculate_fee(amount, load["recife_fee_percent"] or 0.0)
            net_amount = round(amount - slv_fee - recife_fee, 2)
            if load["driver_id"]:
                driver_totals[load["driver_id"]] = driver_totals.get(load["driver_id"], 0.0) + net_amount
            if load["owner_id"]:
                owner_totals[load["owner_id"]] = owner_totals.get(load["owner_id"], 0.0) + net_amount

        entry_date = date.today().isoformat()
        description = f"Fechamento semana {week_reference}"
        for driver_id, total in driver_totals.items():
            exists = self.repository.ledger_entry_exists(owner_id=None, driver_id=driver_id, description=description)
            if not exists:
                self.repository.insert_ledger_entry(None, driver_id, entry_date, total, description)
        for owner_id, total in owner_totals.items():
            exists = self.repository.ledger_entry_exists(owner_id=owner_id, driver_id=None, description=description)
            if not exists:
                self.repository.insert_ledger_entry(owner_id, None, entry_date, total, description)
        return {
            "drivers": sum(driver_totals.values()),
            "owners": sum(owner_totals.values()),
            "loads": len(loads),
        }

    def get_ledger(
        self,
        owner_external_id: str | None = None,
        driver_external_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, str]]:
        rows = self.repository.get_ledger_rows(owner_external_id, driver_external_id, limit)
        return [dict(row) for row in rows]

    def build_summary(self) -> dict[str, float]:
        stats, expenses, pending = self.repository.get_summary_stats()
        total_credit = stats["total_credit"] or 0.0
        total_debit = stats["total_debit"] or 0.0
        total_expenses = expenses["total_expenses"] or 0.0
        balance = round(total_credit - total_debit - total_expenses, 2)
        return {
            "total_credit": total_credit,
            "total_debit": total_debit,
            "total_expenses": total_expenses,
            "balance": balance,
            "pending_loads": pending["pending_count"] or 0,
        }

    def suggest_reconciliation_candidates(self, transaction_external_id: str, limit: int = 5) -> list[dict[str, str | float]]:
        txn = self.repository.get_transaction_by_external_id(transaction_external_id)
        if not txn:
            return []
        rows = self.repository.list_open_load_candidates(txn["amount"], txn["txn_date"], limit)
        suggestions: list[dict[str, str | float]] = []
        for row in rows:
            score = max(0, 100 - int((row["amount_gap"] * 2) + (row["day_gap"] * 3)))
            suggestions.append(
                {
                    "load_id": row["external_id"],
                    "load_date": row["load_date"],
                    "amount_gross": row["amount_gross"],
                    "amount_gap": round(row["amount_gap"], 2),
                    "day_gap": round(row["day_gap"], 2),
                    "score": score,
                }
            )
        return suggestions

    def get_open_loads_summary(
        self,
        owner_external_id: str | None = None,
        driver_external_id: str | None = None,
    ) -> dict[str, float | int]:
        row = self.repository.get_open_loads_aggregate(owner_external_id, driver_external_id)
        gross_total = row["gross_total"] or 0.0
        slv_fee_total = row["slv_fee_total"] or 0.0
        recife_fee_total = row["recife_fee_total"] or 0.0
        net_total = round(gross_total - slv_fee_total - recife_fee_total, 2)
        return {
            "open_count": row["open_count"] or 0,
            "gross_total": round(gross_total, 2),
            "slv_fee_total": round(slv_fee_total, 2),
            "recife_fee_total": round(recife_fee_total, 2),
            "net_total": net_total,
        }

    def get_payables_receivables(
        self,
        owner_external_id: str | None = None,
        driver_external_id: str | None = None,
    ) -> dict[str, float]:
        summary = self.get_open_loads_summary(owner_external_id=owner_external_id, driver_external_id=driver_external_id)
        return {
            "receivable": round(float(summary["net_total"]), 2),
            "payable": round(float(summary["recife_fee_total"]), 2),
        }
