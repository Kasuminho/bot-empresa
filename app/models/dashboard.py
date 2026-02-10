from dataclasses import dataclass
from typing import Any


@dataclass
class DashboardData:
    bank_transactions: list[dict[str, Any]]
    loads: list[dict[str, Any]]
    stats: dict[str, Any] | None
    reconciled_count: dict[str, Any] | None
    pending_loads: dict[str, Any] | None
