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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bot Empresa (importações)")
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


if __name__ == "__main__":
    main()
