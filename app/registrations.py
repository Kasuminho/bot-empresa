from app.db import get_connection
from app.importers import parse_amount, parse_date


def add_owner(external_id: str, name: str, telegram_chat_id: str | None) -> int:
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO owners (external_id, name, telegram_chat_id)
        VALUES (?, ?, ?)
        ON CONFLICT(external_id) DO UPDATE SET
            name=excluded.name,
            telegram_chat_id=excluded.telegram_chat_id
        """,
        (external_id, name, telegram_chat_id),
    )
    connection.commit()
    connection.close()
    return cursor.rowcount


def add_driver(
    external_id: str,
    name: str,
    owner_external_id: str | None,
    is_owner_driver: bool,
) -> int:
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO drivers (external_id, name, owner_id, is_owner_driver)
        VALUES (?, ?, (SELECT id FROM owners WHERE external_id = ?), ?)
        ON CONFLICT(external_id) DO UPDATE SET
            name=excluded.name,
            owner_id=excluded.owner_id,
            is_owner_driver=excluded.is_owner_driver
        """,
        (external_id, name, owner_external_id, 1 if is_owner_driver else 0),
    )
    connection.commit()
    connection.close()
    return cursor.rowcount


def add_truck(external_id: str, owner_external_id: str, plate: str | None) -> int:
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO trucks (external_id, owner_id, plate)
        VALUES (?, (SELECT id FROM owners WHERE external_id = ?), ?)
        ON CONFLICT(external_id) DO UPDATE SET
            owner_id=excluded.owner_id,
            plate=excluded.plate
        """,
        (external_id, owner_external_id, plate),
    )
    connection.commit()
    connection.close()
    return cursor.rowcount


def add_bank_account(
    external_id: str,
    label: str,
    owner_external_id: str | None,
    driver_external_id: str | None,
) -> int:
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO bank_accounts (external_id, owner_id, driver_id, label)
        VALUES (
            ?,
            (SELECT id FROM owners WHERE external_id = ?),
            (SELECT id FROM drivers WHERE external_id = ?),
            ?
        )
        ON CONFLICT(external_id) DO UPDATE SET
            owner_id=excluded.owner_id,
            driver_id=excluded.driver_id,
            label=excluded.label
        """,
        (external_id, owner_external_id, driver_external_id, label),
    )
    connection.commit()
    connection.close()
    return cursor.rowcount


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
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO loads (
            external_id,
            driver_id,
            truck_id,
            load_date,
            description,
            amount_gross,
            slv_fee_percent,
            recife_fee_percent,
            status,
            week_reference,
            sheet_owner,
            updated_at
        )
        VALUES (
            ?,
            (SELECT id FROM drivers WHERE external_id = ?),
            (SELECT id FROM trucks WHERE external_id = ?),
            ?,
            ?,
            ?,
            ?,
            ?,
            COALESCE(?, 'open'),
            ?,
            ?,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT(external_id) DO UPDATE SET
            driver_id=excluded.driver_id,
            truck_id=excluded.truck_id,
            load_date=excluded.load_date,
            description=excluded.description,
            amount_gross=excluded.amount_gross,
            slv_fee_percent=excluded.slv_fee_percent,
            recife_fee_percent=excluded.recife_fee_percent,
            status=excluded.status,
            week_reference=excluded.week_reference,
            sheet_owner=excluded.sheet_owner,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
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
        ),
    )
    connection.commit()
    connection.close()
    return cursor.rowcount


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
    connection = get_connection()
    cursor = connection.cursor()
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
        VALUES (
            (SELECT id FROM owners WHERE external_id = ?),
            (SELECT id FROM trucks WHERE external_id = ?),
            (SELECT id FROM bank_accounts WHERE external_id = ?),
            ?,
            ?,
            ?,
            ?,
            ?
        )
        """,
        (
            owner_external_id,
            truck_external_id,
            bank_account_external_id,
            parse_date(expense_date) or expense_date,
            parse_amount(amount),
            description,
            category,
            cost_center,
        ),
    )
    connection.commit()
    connection.close()
    return cursor.rowcount


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
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO bank_transactions (
            external_id,
            account_id,
            txn_date,
            description,
            amount,
            transaction_type,
            category,
            related_account_id,
            sheet_owner
        )
        VALUES (
            ?,
            (SELECT id FROM bank_accounts WHERE external_id = ?),
            ?,
            ?,
            ?,
            ?,
            ?,
            (SELECT id FROM bank_accounts WHERE external_id = ?),
            ?
        )
        ON CONFLICT(external_id) DO UPDATE SET
            account_id=excluded.account_id,
            txn_date=excluded.txn_date,
            description=excluded.description,
            amount=excluded.amount,
            transaction_type=excluded.transaction_type,
            category=excluded.category,
            related_account_id=excluded.related_account_id,
            sheet_owner=excluded.sheet_owner
        """,
        (
            external_id,
            account_external_id,
            parse_date(txn_date) or txn_date,
            description,
            parse_amount(amount),
            transaction_type or "credit",
            category,
            related_account_external_id,
            sheet_owner,
        ),
    )
    connection.commit()
    connection.close()
    return cursor.rowcount
