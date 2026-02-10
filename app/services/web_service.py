from app.models.dashboard import DashboardData
from app.repositories.dashboard_repository import DashboardRepository


class WebService:
    def __init__(self, repository: DashboardRepository | None = None) -> None:
        self.repository = repository or DashboardRepository()

    def fetch_dashboard(self) -> DashboardData:
        return self.repository.fetch_dashboard()

    def reconcile(
        self,
        bank_transaction_id: int,
        reconciliation_type: str,
        notes: str | None,
        load_ids: list[int] | None,
    ) -> None:
        self.repository.reconcile(bank_transaction_id, reconciliation_type, notes, load_ids)
