from app.services.finance_service import FinanceService

_service = FinanceService()


def ensure_dispatcher_fee_expense(load_external_id: str, connection=None) -> None:
    _service.ensure_dispatcher_fee_expense(load_external_id, connection=connection)


def close_week(week_reference: str) -> dict[str, float]:
    return _service.close_week(week_reference)


def get_ledger(
    owner_external_id: str | None = None,
    driver_external_id: str | None = None,
    limit: int = 10,
) -> list[dict[str, str]]:
    return _service.get_ledger(owner_external_id=owner_external_id, driver_external_id=driver_external_id, limit=limit)


def build_summary() -> dict[str, float]:
    return _service.build_summary()


def suggest_reconciliation_candidates(transaction_external_id: str, limit: int = 5) -> list[dict[str, str | float]]:
    return _service.suggest_reconciliation_candidates(transaction_external_id, limit)


def get_open_loads_summary(
    owner_external_id: str | None = None,
    driver_external_id: str | None = None,
) -> dict[str, float | int]:
    return _service.get_open_loads_summary(owner_external_id=owner_external_id, driver_external_id=driver_external_id)


def get_payables_receivables(
    owner_external_id: str | None = None,
    driver_external_id: str | None = None,
) -> dict[str, float]:
    return _service.get_payables_receivables(owner_external_id=owner_external_id, driver_external_id=driver_external_id)
