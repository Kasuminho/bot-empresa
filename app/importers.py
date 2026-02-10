import csv
from datetime import datetime
from pathlib import Path

from app.db import get_connection
from app.finance import ensure_dispatcher_fee_expense

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]


def parse_date(value: str | None) -> str | None:
    if not value:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"Data inválida: {value}")


def parse_amount(value: str | None) -> float:
    if value is None:
        return 0.0
    cleaned = (
        value.replace(" ", "")
        .replace("R$", "")
        .replace("$", "")
        .strip()
    )
    if "," in cleaned and "." in cleaned:
        if cleaned.find(",") < cleaned.find("."):
            cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    return float(cleaned)


def _read_csv(path: Path | str) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        return list(reader)


def import_owners(path: Path | str) -> int:
    rows = _read_csv(path)
    connection = get_connection()
    cursor = connection.cursor()
    for row in rows:
        cursor.execute(
            """
            INSERT INTO owners (external_id, name, telegram_chat_id)
            VALUES (%s, %s, %s)
            ON CONFLICT(external_id) DO UPDATE SET
                name=excluded.name,
                telegram_chat_id=excluded.telegram_chat_id
            """,
            (row.get("owner_id"), row.get("name"), row.get("telegram_chat_id")),
        )
    connection.commit()
    connection.close()
    return len(rows)


def import_drivers(path: Path | str) -> int:
    rows = _read_csv(path)
    connection = get_connection()
    cursor = connection.cursor()
    for row in rows:
        owner_id = row.get("owner_id")
        cursor.execute(
            """
            INSERT INTO drivers (external_id, name, owner_id, is_owner_driver)
            VALUES (%s, %s, (SELECT id FROM owners WHERE external_id = %s), %s)
            ON CONFLICT(external_id) DO UPDATE SET
                name=excluded.name,
                owner_id=excluded.owner_id,
                is_owner_driver=excluded.is_owner_driver
            """,
            (
                row.get("driver_id"),
                row.get("name"),
                owner_id,
                1 if row.get("is_owner_driver") == "1" else 0,
            ),
        )
    connection.commit()
    connection.close()
    return len(rows)


def import_trucks(path: Path | str) -> int:
    rows = _read_csv(path)
    connection = get_connection()
    cursor = connection.cursor()
    for row in rows:
        cursor.execute(
            """
            INSERT INTO trucks (external_id, owner_id, plate)
            VALUES (%s, (SELECT id FROM owners WHERE external_id = %s), %s)
            ON CONFLICT(external_id) DO UPDATE SET
                owner_id=excluded.owner_id,
                plate=excluded.plate
            """,
            (row.get("truck_id"), row.get("owner_id"), row.get("plate")),
        )
    connection.commit()
    connection.close()
    return len(rows)


def import_bank_accounts(path: Path | str) -> int:
    rows = _read_csv(path)
    connection = get_connection()
    cursor = connection.cursor()
    for row in rows:
        cursor.execute(
            """
            INSERT INTO bank_accounts (external_id, owner_id, driver_id, label)
            VALUES (
                %s,
                (SELECT id FROM owners WHERE external_id = %s),
                (SELECT id FROM drivers WHERE external_id = %s),
                %s
            )
            ON CONFLICT(external_id) DO UPDATE SET
                owner_id=excluded.owner_id,
                driver_id=excluded.driver_id,
                label=excluded.label
            """,
            (
                row.get("account_id"),
                row.get("owner_id"),
                row.get("driver_id"),
                row.get("label"),
            ),
        )
    connection.commit()
    connection.close()
    return len(rows)


def import_loads(path: Path | str, sheet_owner: str | None = None) -> int:
    rows = _read_csv(path)
    connection = get_connection()
    cursor = connection.cursor()
    for row in rows:
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
                %s,
                (SELECT id FROM drivers WHERE external_id = %s),
                (SELECT id FROM trucks WHERE external_id = %s),
                %s,
                %s,
                %s,
                %s,
                %s,
                COALESCE(%s, 'open'),
                %s,
                %s,
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
                row.get("load_id"),
                row.get("driver_id"),
                row.get("truck_id"),
                parse_date(row.get("load_date")),
                row.get("description"),
                parse_amount(row.get("amount_gross")),
                parse_amount(row.get("slv_fee_percent")) if row.get("slv_fee_percent") else 0.0,
                parse_amount(row.get("recife_fee_percent")) if row.get("recife_fee_percent") else 10.0,
                row.get("status"),
                row.get("week_reference"),
                sheet_owner,
            ),
        )
        ensure_dispatcher_fee_expense(row.get("load_id"), connection=connection)
    connection.commit()
    connection.close()
    return len(rows)


def import_car_loads(
    path: Path | str,
    truck_external_id: str,
    sheet_owner: str | None = None,
) -> int:
    rows = _read_csv(path)
    connection = get_connection()
    cursor = connection.cursor()
    for row in rows:
        cursor.execute(
            """
            INSERT INTO loads (
                external_id,
                truck_id,
                load_date,
                description,
                amount_gross,
                recife_fee_percent,
                status,
                sheet_owner,
                updated_at
            )
            VALUES (
                %s,
                (SELECT id FROM trucks WHERE external_id = %s),
                %s,
                %s,
                %s,
                %s,
                COALESCE(%s, 'open'),
                %s,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT(external_id) DO UPDATE SET
                truck_id=excluded.truck_id,
                load_date=excluded.load_date,
                description=excluded.description,
                amount_gross=excluded.amount_gross,
                recife_fee_percent=excluded.recife_fee_percent,
                status=excluded.status,
                sheet_owner=excluded.sheet_owner,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                row.get("Order ID"),
                truck_external_id,
                parse_date(row.get("Delivery Date")) or parse_date(row.get("Pickup Date")),
                row.get("EMPRESA"),
                parse_amount(row.get("RATE")),
                parse_amount(row.get("DISPATCHER FEE")) if row.get("DISPATCHER FEE") else 10.0,
                "open",
                sheet_owner,
            ),
        )
        ensure_dispatcher_fee_expense(row.get("Order ID"), connection=connection)
    connection.commit()
    connection.close()
    return len(rows)

def import_bank_transactions(path: Path | str, sheet_owner: str | None = None) -> int:
    rows = _read_csv(path)
    connection = get_connection()
    cursor = connection.cursor()
    for row in rows:
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
                %s,
                (SELECT id FROM bank_accounts WHERE external_id = %s),
                %s,
                %s,
                %s,
                %s,
                %s,
                (SELECT id FROM bank_accounts WHERE external_id = %s),
                %s
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
                row.get("transaction_id"),
                row.get("account_id"),
                parse_date(row.get("txn_date")) or row.get("txn_date"),
                row.get("description"),
                parse_amount(row.get("amount")),
                row.get("transaction_type") or "credit",
                row.get("category"),
                row.get("related_account_id"),
                sheet_owner,
            ),
        )
    connection.commit()
    connection.close()
    return len(rows)


def import_expenses(path: Path | str) -> int:
    rows = _read_csv(path)
    connection = get_connection()
    cursor = connection.cursor()
    for row in rows:
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
                (SELECT id FROM owners WHERE external_id = %s),
                (SELECT id FROM trucks WHERE external_id = %s),
                (SELECT id FROM bank_accounts WHERE external_id = %s),
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                row.get("owner_id"),
                row.get("truck_id"),
                row.get("account_id"),
                parse_date(row.get("expense_date")) or row.get("expense_date"),
                parse_amount(row.get("amount")),
                row.get("description"),
                row.get("category"),
                row.get("cost_center"),
            ),
        )
    connection.commit()
    connection.close()
    return len(rows)
