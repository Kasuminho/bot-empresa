from app.services.registration_service import RegistrationService

_service = RegistrationService()


def add_owner(external_id: str, name: str, telegram_chat_id: str | None) -> int:
    return _service.add_owner(external_id, name, telegram_chat_id)


def add_driver(
    external_id: str,
    name: str,
    owner_external_id: str | None,
    is_owner_driver: bool,
) -> int:
    return _service.add_driver(external_id, name, owner_external_id, is_owner_driver)


def add_truck(external_id: str, owner_external_id: str, plate: str | None) -> int:
    return _service.add_truck(external_id, owner_external_id, plate)


def add_bank_account(
    external_id: str,
    label: str,
    owner_external_id: str | None,
    driver_external_id: str | None,
) -> int:
    return _service.add_bank_account(external_id, label, owner_external_id, driver_external_id)


def add_load(
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
    return _service.add_load(
        external_id,
        driver_external_id,
        truck_external_id,
        load_date,
        description,
        amount_gross,
        slv_fee_percent,
        recife_fee_percent,
        status,
        week_reference,
        sheet_owner,
    )


def add_expense(
    owner_external_id: str | None,
    truck_external_id: str | None,
    bank_account_external_id: str | None,
    expense_date: str,
    amount: str,
    description: str | None,
    category: str | None,
    cost_center: str | None,
) -> int:
    return _service.add_expense(
        owner_external_id,
        truck_external_id,
        bank_account_external_id,
        expense_date,
        amount,
        description,
        category,
        cost_center,
    )


def add_bank_transaction(
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
    return _service.add_bank_transaction(
        external_id,
        account_external_id,
        txn_date,
        description,
        amount,
        transaction_type,
        category,
        related_account_external_id,
        sheet_owner,
    )
