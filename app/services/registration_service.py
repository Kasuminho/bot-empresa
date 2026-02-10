from app.finance import ensure_dispatcher_fee_expense
from app.importers import parse_amount, parse_date
from app.repositories.registration_repository import RegistrationRepository


class RegistrationService:
    def __init__(self, repository: RegistrationRepository | None = None) -> None:
        self.repository = repository or RegistrationRepository()

    def add_owner(self, external_id: str, name: str, telegram_chat_id: str | None) -> int:
        return self.repository.upsert_owner(external_id, name, telegram_chat_id)

    def add_driver(
        self,
        external_id: str,
        name: str,
        owner_external_id: str | None,
        is_owner_driver: bool,
    ) -> int:
        return self.repository.upsert_driver(external_id, name, owner_external_id, is_owner_driver)

    def add_truck(self, external_id: str, owner_external_id: str, plate: str | None) -> int:
        return self.repository.upsert_truck(external_id, owner_external_id, plate)

    def add_bank_account(
        self,
        external_id: str,
        label: str,
        owner_external_id: str | None,
        driver_external_id: str | None,
    ) -> int:
        return self.repository.upsert_bank_account(external_id, label, owner_external_id, driver_external_id)

    def add_load(
        self,
        external_id: str,
        driver_external_id: str | None,
        truck_external_id: str | None,
        load_date: str | None,
        description: str | None,
        amount_gross: str,
        slv_fee_percent: str | None,
        recife_fee_percent: str | None,
        status: str | None,
        week_reference: str | None,
        sheet_owner: str | None,
    ) -> int:
        count = self.repository.upsert_load(
            external_id,
            driver_external_id,
            truck_external_id,
            parse_date(load_date) if load_date else None,
            description,
            parse_amount(amount_gross),
            parse_amount(slv_fee_percent) if slv_fee_percent else 0.0,
            parse_amount(recife_fee_percent) if recife_fee_percent else 10.0,
            status,
            week_reference,
            sheet_owner,
        )
        ensure_dispatcher_fee_expense(external_id)
        return count

    def add_expense(
        self,
        owner_external_id: str | None,
        truck_external_id: str | None,
        bank_account_external_id: str | None,
        expense_date: str,
        amount: str,
        description: str | None,
        category: str | None,
        cost_center: str | None,
    ) -> int:
        return self.repository.insert_expense(
            owner_external_id,
            truck_external_id,
            bank_account_external_id,
            parse_date(expense_date) or expense_date,
            parse_amount(amount),
            description,
            category,
            cost_center,
        )

    def add_bank_transaction(
        self,
        external_id: str,
        account_external_id: str | None,
        txn_date: str,
        description: str | None,
        amount: str,
        transaction_type: str | None,
        category: str | None,
        related_account_external_id: str | None,
        sheet_owner: str | None,
    ) -> int:
        return self.repository.upsert_bank_transaction(
            external_id,
            account_external_id,
            parse_date(txn_date) or txn_date,
            description,
            parse_amount(amount),
            transaction_type or "credit",
            category,
            related_account_external_id,
            sheet_owner,
        )
