import argparse
from pathlib import Path

from app.db import init_db
from app.importers import (
    import_bank_accounts,
    import_bank_transactions,
    import_car_loads,
    import_drivers,
    import_expenses,
    import_loads,
    import_owners,
    import_trucks,
)
from app.config import TELEGRAM_CHAT_ID, TELEGRAM_TOKEN
from app.registrations import (
    add_bank_account,
    add_bank_transaction,
    add_driver,
    add_expense,
    add_load,
    add_owner,
    add_truck,
)
from app.telegram import send_message


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bot Empresa CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db")

    import_bank = subparsers.add_parser("import-bank")
    import_bank.add_argument("path", type=Path)
    import_bank.add_argument("--sheet-owner", type=str, default=None)

    import_load = subparsers.add_parser("import-loads")
    import_load.add_argument("path", type=Path)
    import_load.add_argument("--sheet-owner", type=str, default=None)

    import_car = subparsers.add_parser("import-car-loads")
    import_car.add_argument("path", type=Path)
    import_car.add_argument("--truck-id", required=True)
    import_car.add_argument("--sheet-owner", type=str, default=None)

    import_driver = subparsers.add_parser("import-drivers")
    import_driver.add_argument("path", type=Path)

    import_owner = subparsers.add_parser("import-owners")
    import_owner.add_argument("path", type=Path)

    import_truck = subparsers.add_parser("import-trucks")
    import_truck.add_argument("path", type=Path)

    import_account = subparsers.add_parser("import-accounts")
    import_account.add_argument("path", type=Path)

    import_expense = subparsers.add_parser("import-expenses")
    import_expense.add_argument("path", type=Path)

    add_owner_cmd = subparsers.add_parser("add-owner")
    add_owner_cmd.add_argument("--owner-id", required=True)
    add_owner_cmd.add_argument("--name", required=True)
    add_owner_cmd.add_argument("--telegram-chat-id")

    add_driver_cmd = subparsers.add_parser("add-driver")
    add_driver_cmd.add_argument("--driver-id", required=True)
    add_driver_cmd.add_argument("--name", required=True)
    add_driver_cmd.add_argument("--owner-id")
    add_driver_cmd.add_argument("--is-owner-driver", action="store_true")

    add_truck_cmd = subparsers.add_parser("add-truck")
    add_truck_cmd.add_argument("--truck-id", required=True)
    add_truck_cmd.add_argument("--owner-id", required=True)
    add_truck_cmd.add_argument("--plate")

    add_account_cmd = subparsers.add_parser("add-account")
    add_account_cmd.add_argument("--account-id", required=True)
    add_account_cmd.add_argument("--label", required=True)
    add_account_cmd.add_argument("--owner-id")
    add_account_cmd.add_argument("--driver-id")

    add_load_cmd = subparsers.add_parser("add-load")
    add_load_cmd.add_argument("--load-id", required=True)
    add_load_cmd.add_argument("--driver-id")
    add_load_cmd.add_argument("--truck-id")
    add_load_cmd.add_argument("--load-date")
    add_load_cmd.add_argument("--description")
    add_load_cmd.add_argument("--amount-gross", required=True)
    add_load_cmd.add_argument("--slv-fee-percent")
    add_load_cmd.add_argument("--recife-fee-percent")
    add_load_cmd.add_argument("--status")
    add_load_cmd.add_argument("--week-reference")
    add_load_cmd.add_argument("--sheet-owner")

    add_expense_cmd = subparsers.add_parser("add-expense")
    add_expense_cmd.add_argument("--owner-id")
    add_expense_cmd.add_argument("--truck-id")
    add_expense_cmd.add_argument("--account-id")
    add_expense_cmd.add_argument("--expense-date", required=True)
    add_expense_cmd.add_argument("--amount", required=True)
    add_expense_cmd.add_argument("--description")
    add_expense_cmd.add_argument("--category")
    add_expense_cmd.add_argument("--cost-center")

    add_bank_cmd = subparsers.add_parser("add-bank-transaction")
    add_bank_cmd.add_argument("--transaction-id", required=True)
    add_bank_cmd.add_argument("--account-id")
    add_bank_cmd.add_argument("--txn-date", required=True)
    add_bank_cmd.add_argument("--description")
    add_bank_cmd.add_argument("--amount", required=True)
    add_bank_cmd.add_argument("--transaction-type")
    add_bank_cmd.add_argument("--category")
    add_bank_cmd.add_argument("--related-account-id")
    add_bank_cmd.add_argument("--sheet-owner")

    telegram_cmd = subparsers.add_parser("send-telegram")
    telegram_cmd.add_argument("--token", default=TELEGRAM_TOKEN)
    telegram_cmd.add_argument("--chat-id", default=TELEGRAM_CHAT_ID)
    telegram_cmd.add_argument("--text", required=True)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init-db":
        init_db()
        print("Banco de dados inicializado.")
    elif args.command == "import-bank":
        count = import_bank_transactions(args.path, sheet_owner=args.sheet_owner)
        print(f"{count} transações bancárias importadas.")
    elif args.command == "import-loads":
        count = import_loads(args.path, sheet_owner=args.sheet_owner)
        print(f"{count} loads importados.")
    elif args.command == "import-car-loads":
        count = import_car_loads(
            args.path,
            truck_external_id=args.truck_id,
            sheet_owner=args.sheet_owner,
        )
        print(f"{count} loads de carros importados.")
    elif args.command == "import-drivers":
        count = import_drivers(args.path)
        print(f"{count} motoristas importados.")
    elif args.command == "import-owners":
        count = import_owners(args.path)
        print(f"{count} donos importados.")
    elif args.command == "import-trucks":
        count = import_trucks(args.path)
        print(f"{count} trucks importados.")
    elif args.command == "import-accounts":
        count = import_bank_accounts(args.path)
        print(f"{count} contas bancárias importadas.")
    elif args.command == "import-expenses":
        count = import_expenses(args.path)
        print(f"{count} despesas importadas.")
    elif args.command == "add-owner":
        count = add_owner(args.owner_id, args.name, args.telegram_chat_id)
        print(f"{count} dono cadastrado.")
    elif args.command == "add-driver":
        count = add_driver(
            args.driver_id,
            args.name,
            args.owner_id,
            args.is_owner_driver,
        )
        print(f"{count} motorista cadastrado.")
    elif args.command == "add-truck":
        count = add_truck(args.truck_id, args.owner_id, args.plate)
        print(f"{count} truck cadastrado.")
    elif args.command == "add-account":
        count = add_bank_account(
            args.account_id,
            args.label,
            args.owner_id,
            args.driver_id,
        )
        print(f"{count} conta bancária cadastrada.")
    elif args.command == "add-load":
        count = add_load(
            args.load_id,
            args.driver_id,
            args.truck_id,
            args.load_date,
            args.description,
            args.amount_gross,
            args.slv_fee_percent,
            args.recife_fee_percent,
            args.status,
            args.week_reference,
            args.sheet_owner,
        )
        print(f"{count} load cadastrado.")
    elif args.command == "add-expense":
        count = add_expense(
            args.owner_id,
            args.truck_id,
            args.account_id,
            args.expense_date,
            args.amount,
            args.description,
            args.category,
            args.cost_center,
        )
        print(f"{count} despesa cadastrada.")
    elif args.command == "add-bank-transaction":
        count = add_bank_transaction(
            args.transaction_id,
            args.account_id,
            args.txn_date,
            args.description,
            args.amount,
            args.transaction_type,
            args.category,
            args.related_account_id,
            args.sheet_owner,
        )
        print(f"{count} transação bancária cadastrada.")
    elif args.command == "send-telegram":
        if not args.token or not args.chat_id:
            raise SystemExit(
                "Defina --token e --chat-id ou configure "
                "BOT_TELEGRAM_TOKEN e BOT_TELEGRAM_CHAT_ID no .env."
            )
        send_message(args.token, args.chat_id, args.text)
        print("Mensagem enviada.")


if __name__ == "__main__":
    main()
