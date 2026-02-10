import shlex
import tempfile
from uuid import uuid4
from typing import Any

import requests

from app.config import TELEGRAM_ADMIN_CHAT_IDS, TELEGRAM_TOKEN
from app.finance import (
    build_summary,
    close_week,
    get_ledger,
    get_open_loads_summary,
    get_payables_receivables,
    suggest_reconciliation_candidates,
)
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
from app.repositories.telegram_repository import TelegramRepository
from app.registrations import (
    add_bank_account,
    add_bank_transaction,
    add_driver,
    add_expense,
    add_load,
    add_owner,
    add_truck,
)


class TelegramService:
    def __init__(self, repository: TelegramRepository | None = None) -> None:
        self.repository = repository or TelegramRepository()
        self.pending_confirmations: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _csv_required_headers() -> dict[str, set[str]]:
        return {
            "/import_owners": {"owner_id", "name"},
            "/import_drivers": {"driver_id", "name"},
            "/import_trucks": {"truck_id", "owner_id"},
            "/import_accounts": {"account_id", "label"},
            "/import_loads": {"load_id", "amount_gross"},
            "/import_bank": {"transaction_id", "txn_date", "amount"},
            "/import_expenses": {"expense_date", "amount"},
            "/import_car_loads": {"Order ID", "RATE"},
        }

    @staticmethod
    def send_message(token: str, chat_id: str, text: str) -> None:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
        response.raise_for_status()

    def send_bot_message(self, chat_id: str, text: str) -> None:
        if not TELEGRAM_TOKEN:
            raise RuntimeError("BOT_TELEGRAM_TOKEN não configurado.")
        self.send_message(TELEGRAM_TOKEN, chat_id, text)

    def _fetch_file(self, file_id: str) -> bytes:
        if not TELEGRAM_TOKEN:
            raise RuntimeError("BOT_TELEGRAM_TOKEN não configurado.")
        info_response = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile",
            params={"file_id": file_id},
            timeout=10,
        )
        info_response.raise_for_status()
        payload = info_response.json()
        file_path = payload.get("result", {}).get("file_path")
        if not file_path:
            raise RuntimeError("Arquivo não encontrado no Telegram.")
        file_response = requests.get(
            f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}",
            timeout=10,
        )
        file_response.raise_for_status()
        return file_response.content

    @staticmethod
    def _parse_kv_args(text: str) -> dict[str, str]:
        args: dict[str, str] = {}
        for token in shlex.split(text):
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            args[key.strip()] = value.strip()
        return args

    @staticmethod
    def help_message() -> str:
        return (
            "Comandos disponíveis:\n"
            "/add_owner name=\"Nome\" owner_id=opcional telegram_chat_id=...\n"
            "/add_driver name=\"Nome\" driver_id=opcional owner_id=... is_owner_driver=0|1\n"
            "/add_truck owner_id=... truck_id=opcional plate=...\n"
            "/add_account label=\"Conta\" account_id=opcional owner_id=... driver_id=...\n"
            "/add_load amount_gross=... load_id=opcional driver_id=... truck_id=... load_date=YYYY-MM-DD\n"
            "/add_expense owner_id=... truck_id=... account_id=... expense_date=YYYY-MM-DD amount=...\n"
            "/add_bank_transaction txn_date=YYYY-MM-DD amount=... transaction_id=opcional account_id=...\n"
            "/summary\n"
            "/close_week week_reference=2024-W27\n"
            "/ledger owner_id=OWNER_01 limit=10\n"
            "/open_loads owner_id=OWNER_01\n"
            "/balance owner_id=OWNER_01\n"
            "/suggest_reconcile transaction_id=TXN_01\n"
            "/subscribe_summary\n"
            "/unsubscribe_summary\n"
            "/authorize chat_id=123 role=operator (apenas admin)\n"
            "Confirmações: /confirm e /cancel\n"
            "Importação via CSV (envie o arquivo com a legenda): /import_*"
        )

    @staticmethod
    def _ensure_external_id(args: dict[str, str], key: str, prefix: str) -> str:
        value = args.get(key)
        if value:
            return value
        generated = f"{prefix}_{uuid4().hex[:8].upper()}"
        args[key] = generated
        return generated

    def _upsert_authorized_user(self, chat_id: str, username: str | None, role: str = "operator") -> None:
        self.repository.upsert_authorized_user(chat_id, username, role)

    def _is_authorized(self, chat_id: str) -> bool:
        if chat_id in TELEGRAM_ADMIN_CHAT_IDS:
            return True
        return self.repository.is_authorized(chat_id)

    def _role_for(self, chat_id: str) -> str | None:
        if chat_id in TELEGRAM_ADMIN_CHAT_IDS:
            return "admin"
        return self.repository.get_role(chat_id)

    def _audit(
        self,
        chat_id: str,
        username: str | None,
        command: str,
        payload: str,
        status: str,
        error: str | None = None,
    ) -> None:
        self.repository.create_audit_log(chat_id, username, command, payload, status, error)

    def _validate_csv_headers(self, command: str, file_bytes: bytes) -> None:
        required = self._csv_required_headers().get(command)
        if not required:
            return
        first_line = file_bytes.decode("utf-8-sig", errors="ignore").splitlines()[0] if file_bytes else ""
        headers = {item.strip() for item in first_line.split(",") if item.strip()}
        missing = required - headers
        if missing:
            raise ValueError(f"CSV inválido para {command}. Faltando colunas: {', '.join(sorted(missing))}")

    def _queue_confirmation(self, chat_id: str, action: str, args: dict[str, str]) -> None:
        self.pending_confirmations[chat_id] = {"action": action, "args": args}

    def _execute_confirmed(self, chat_id: str) -> str:
        pending = self.pending_confirmations.get(chat_id)
        if not pending:
            return "Não existe ação pendente."
        action = pending["action"]
        args = pending["args"]
        if action == "add_load":
            add_load(
                args["load_id"],
                args.get("driver_id"),
                args.get("truck_id"),
                args.get("load_date"),
                args.get("description"),
                args["amount_gross"],
                args.get("slv_fee_percent"),
                args.get("recife_fee_percent"),
                args.get("status"),
                args.get("week_reference"),
                args.get("sheet_owner"),
            )
            self.pending_confirmations.pop(chat_id, None)
            return "Load cadastrado com sucesso."
        if action == "close_week":
            result = close_week(args["week_reference"])
            self.pending_confirmations.pop(chat_id, None)
            return (
                "Fechamento concluído:\n"
                f"Semana: {args['week_reference']}\n"
                f"Loads: {result['loads']}\n"
                f"Total motoristas: {result['drivers']}\n"
                f"Total donos: {result['owners']}"
            )
        return "Ação pendente inválida."

    def send_scheduled_summary(self) -> int:
        viewers = self.repository.list_summary_subscribers()
        if not viewers:
            return 0
        summary = build_summary()
        text = (
            "Resumo automático:\n"
            f"Créditos: {summary['total_credit']}\n"
            f"Débitos: {summary['total_debit']}\n"
            f"Despesas: {summary['total_expenses']}\n"
            f"Saldo estimado: {summary['balance']}\n"
            f"Loads pendentes: {summary['pending_loads']}"
        )
        sent = 0
        for row in viewers:
            self.send_bot_message(str(row["chat_id"]), text)
            sent += 1
        return sent

    def handle_update(self, update: dict) -> None:
        message = update.get("message") or update.get("edited_message")
        if not message:
            return
        chat = message.get("chat") or {}
        chat_id = str(chat.get("id")) if chat.get("id") is not None else None
        text = message.get("text") or ""
        caption = message.get("caption") or ""
        document = message.get("document")
        username = message.get("from", {}).get("username")
        if not chat_id:
            return

        if chat_id in TELEGRAM_ADMIN_CHAT_IDS:
            self._upsert_authorized_user(chat_id, username, role="admin")

        command_source = text.strip() if text else caption.strip()
        if not command_source:
            return
        command, *rest = command_source.split(maxsplit=1)
        payload = rest[0] if rest else ""

        try:
            if command in {"/start", "/help"}:
                self.send_bot_message(chat_id, self.help_message())
                self._audit(chat_id, username, command, payload, "ok")
                return

            if not self._is_authorized(chat_id):
                self.send_bot_message(chat_id, "Acesso negado. Peça autorização para o administrador.")
                self._audit(chat_id, username, command, payload, "denied")
                return

            args = self._parse_kv_args(payload)

            if command == "/authorize":
                if self._role_for(chat_id) != "admin":
                    raise ValueError("Apenas admin pode autorizar usuários.")
                target_chat_id = args.get("chat_id")
                role = args.get("role", "operator")
                if not target_chat_id:
                    raise ValueError("Informe chat_id.")
                if role not in {"admin", "operator", "viewer"}:
                    raise ValueError("role inválido.")
                self._upsert_authorized_user(target_chat_id, None, role=role)
                self.send_bot_message(chat_id, f"Usuário {target_chat_id} autorizado como {role}.")
                self._audit(chat_id, username, command, payload, "ok")
                return

            if command == "/subscribe_summary":
                role = self._role_for(chat_id) or "viewer"
                self._upsert_authorized_user(chat_id, username, role=role)
                self.repository.upsert_summary_subscription(chat_id)
                self.send_bot_message(chat_id, "Inscrição em resumo automático ativada.")
                self._audit(chat_id, username, command, payload, "ok")
                return

            if command == "/unsubscribe_summary":
                self.repository.delete_subscription(chat_id)
                self.send_bot_message(chat_id, "Inscrição removida.")
                self._audit(chat_id, username, command, payload, "ok")
                return

            if command == "/confirm":
                result_text = self._execute_confirmed(chat_id)
                self.send_bot_message(chat_id, result_text)
                self._audit(chat_id, username, command, payload, "ok")
                return

            if command == "/cancel":
                self.pending_confirmations.pop(chat_id, None)
                self.send_bot_message(chat_id, "Ação pendente cancelada.")
                self._audit(chat_id, username, command, payload, "ok")
                return

            if command == "/summary":
                summary = build_summary()
                self.send_bot_message(
                    chat_id,
                    "Resumo:\n"
                    f"Créditos: {summary['total_credit']}\n"
                    f"Débitos: {summary['total_debit']}\n"
                    f"Despesas: {summary['total_expenses']}\n"
                    f"Saldo estimado: {summary['balance']}\n"
                    f"Loads pendentes: {summary['pending_loads']}",
                )
                self._audit(chat_id, username, command, payload, "ok")
                return

            if command == "/close_week":
                week_reference = args.get("week_reference")
                if not week_reference:
                    raise ValueError("Informe week_reference.")
                self._queue_confirmation(chat_id, "close_week", {"week_reference": week_reference})
                self.send_bot_message(
                    chat_id,
                    f"Confirmar fechamento da semana {week_reference}? Use /confirm ou /cancel.",
                )
                self._audit(chat_id, username, command, payload, "pending")
                return

            if command == "/ledger":
                owner_id = args.get("owner_id")
                driver_id = args.get("driver_id")
                limit = int(args.get("limit", "10"))
                entries = get_ledger(
                    owner_external_id=owner_id,
                    driver_external_id=driver_id,
                    limit=limit,
                )
                if not entries:
                    self.send_bot_message(chat_id, "Sem lançamentos no período.")
                    self._audit(chat_id, username, command, payload, "ok")
                    return
                lines = [
                    f"{item['entry_date']} | {item['entry_type']} | {item['amount']} | {item['description']}"
                    for item in entries
                ]
                self.send_bot_message(chat_id, "Lançamentos:\n" + "\n".join(lines))
                self._audit(chat_id, username, command, payload, "ok")
                return

            if command == "/open_loads":
                owner_id = args.get("owner_id")
                driver_id = args.get("driver_id")
                if not owner_id and not driver_id:
                    raise ValueError("Informe owner_id ou driver_id.")
                summary = get_open_loads_summary(
                    owner_external_id=owner_id,
                    driver_external_id=driver_id,
                )
                self.send_bot_message(
                    chat_id,
                    "Loads em aberto:\n"
                    f"Quantidade: {summary['open_count']}\n"
                    f"Total bruto: {summary['gross_total']}\n"
                    f"SLV fee: {summary['slv_fee_total']}\n"
                    f"Dispatcher fee: {summary['recife_fee_total']}\n"
                    f"Total líquido: {summary['net_total']}",
                )
                self._audit(chat_id, username, command, payload, "ok")
                return

            if command == "/balance":
                owner_id = args.get("owner_id")
                driver_id = args.get("driver_id")
                if not owner_id and not driver_id:
                    raise ValueError("Informe owner_id ou driver_id.")
                totals = get_payables_receivables(
                    owner_external_id=owner_id,
                    driver_external_id=driver_id,
                )
                self.send_bot_message(
                    chat_id,
                    "Resumo financeiro:\n"
                    f"A receber: {totals['receivable']}\n"
                    f"A pagar (dispatcher): {totals['payable']}",
                )
                self._audit(chat_id, username, command, payload, "ok")
                return

            if command == "/suggest_reconcile":
                transaction_id = args.get("transaction_id")
                if not transaction_id:
                    raise ValueError("Informe transaction_id.")
                suggestions = suggest_reconciliation_candidates(transaction_id)
                if not suggestions:
                    self.send_bot_message(chat_id, "Sem sugestões para essa transação.")
                    self._audit(chat_id, username, command, payload, "ok")
                    return
                lines = [
                    f"Load {item['load_id']} | score {item['score']} | gap {item['amount_gap']} | day_gap {item['day_gap']}"
                    for item in suggestions
                ]
                self.send_bot_message(chat_id, "Sugestões:\n" + "\n".join(lines))
                self._audit(chat_id, username, command, payload, "ok")
                return

            if command.startswith("/import_"):
                if not document:
                    raise ValueError("Envie o CSV anexado com a legenda do comando.")
                file_bytes = self._fetch_file(document["file_id"])
                self._validate_csv_headers(command, file_bytes)
                if args.get("dry_run") == "1":
                    self.send_bot_message(chat_id, "Dry-run OK: CSV válido para importação.")
                    self._audit(chat_id, username, command, payload, "ok")
                    return
                with tempfile.NamedTemporaryFile(suffix=".csv") as tmp_file:
                    tmp_file.write(file_bytes)
                    tmp_file.flush()
                    if command == "/import_owners":
                        count = import_owners(tmp_file.name)
                    elif command == "/import_drivers":
                        count = import_drivers(tmp_file.name)
                    elif command == "/import_trucks":
                        count = import_trucks(tmp_file.name)
                    elif command == "/import_accounts":
                        count = import_bank_accounts(tmp_file.name)
                    elif command == "/import_loads":
                        count = import_loads(tmp_file.name, sheet_owner=args.get("sheet_owner"))
                    elif command == "/import_bank":
                        count = import_bank_transactions(tmp_file.name, sheet_owner=args.get("sheet_owner"))
                    elif command == "/import_expenses":
                        count = import_expenses(tmp_file.name)
                    elif command == "/import_car_loads":
                        truck_id = args.get("truck_id")
                        if not truck_id:
                            raise ValueError("Informe truck_id para importação de carros.")
                        count = import_car_loads(
                            tmp_file.name,
                            truck_external_id=truck_id,
                            sheet_owner=args.get("sheet_owner"),
                        )
                    else:
                        raise ValueError("Importação não reconhecida.")
                self.send_bot_message(chat_id, f"Importação concluída ({count} registros).")
                self._audit(chat_id, username, command, payload, "ok")
                return

            if command == "/add_owner":
                required = {"name"}
                if not required.issubset(args):
                    raise ValueError("Informe name.")
                owner_id = self._ensure_external_id(args, "owner_id", "OWNER")
                telegram_chat_id = args.get("telegram_chat_id") or chat_id
                add_owner(owner_id, args["name"], telegram_chat_id)
                self.send_bot_message(chat_id, f"Dono cadastrado com sucesso. owner_id={owner_id}")
                self._audit(chat_id, username, command, payload, "ok")
                return

            if command == "/add_driver":
                required = {"name"}
                if not required.issubset(args):
                    raise ValueError("Informe name.")
                driver_id = self._ensure_external_id(args, "driver_id", "DRIVER")
                add_driver(driver_id, args["name"], args.get("owner_id"), args.get("is_owner_driver") == "1")
                self.send_bot_message(chat_id, f"Motorista cadastrado com sucesso. driver_id={driver_id}")
                self._audit(chat_id, username, command, payload, "ok")
                return

            if command == "/add_truck":
                required = {"owner_id"}
                if not required.issubset(args):
                    raise ValueError("Informe owner_id.")
                truck_id = self._ensure_external_id(args, "truck_id", "TRUCK")
                add_truck(truck_id, args["owner_id"], args.get("plate"))
                self.send_bot_message(chat_id, f"Truck cadastrado com sucesso. truck_id={truck_id}")
                self._audit(chat_id, username, command, payload, "ok")
                return

            if command == "/add_account":
                required = {"label"}
                if not required.issubset(args):
                    raise ValueError("Informe label.")
                account_id = self._ensure_external_id(args, "account_id", "ACC")
                add_bank_account(account_id, args["label"], args.get("owner_id"), args.get("driver_id"))
                self.send_bot_message(chat_id, f"Conta bancária cadastrada com sucesso. account_id={account_id}")
                self._audit(chat_id, username, command, payload, "ok")
                return

            if command == "/add_load":
                required = {"amount_gross"}
                if not required.issubset(args):
                    raise ValueError("Informe amount_gross.")
                load_id = self._ensure_external_id(args, "load_id", "LOAD")
                self._queue_confirmation(chat_id, "add_load", args)
                self.send_bot_message(
                    chat_id,
                    f"Confirmar cadastro do load {load_id}? Use /confirm ou /cancel.",
                )
                self._audit(chat_id, username, command, payload, "pending")
                return

            if command == "/add_expense":
                required = {"expense_date", "amount"}
                if not required.issubset(args):
                    raise ValueError("Informe expense_date e amount.")
                add_expense(
                    args.get("owner_id"),
                    args.get("truck_id"),
                    args.get("account_id"),
                    args["expense_date"],
                    args["amount"],
                    args.get("description"),
                    args.get("category"),
                    args.get("cost_center"),
                )
                self.send_bot_message(chat_id, "Despesa cadastrada com sucesso.")
                self._audit(chat_id, username, command, payload, "ok")
                return

            if command == "/add_bank_transaction":
                required = {"txn_date", "amount"}
                if not required.issubset(args):
                    raise ValueError("Informe txn_date e amount.")
                transaction_id = self._ensure_external_id(args, "transaction_id", "TXN")
                add_bank_transaction(
                    transaction_id,
                    args.get("account_id"),
                    args["txn_date"],
                    args.get("description"),
                    args["amount"],
                    args.get("transaction_type"),
                    args.get("category"),
                    args.get("related_account_id"),
                    args.get("sheet_owner"),
                )
                self.send_bot_message(chat_id, f"Transação bancária cadastrada com sucesso. transaction_id={transaction_id}")
                self._audit(chat_id, username, command, payload, "ok")
                return

            self.send_bot_message(chat_id, "Comando não reconhecido. Use /help.")
            self._audit(chat_id, username, command, payload, "unknown")
        except Exception as exc:
            self.send_bot_message(chat_id, f"Erro ao processar comando: {exc}")
            self._audit(chat_id, username, command, payload, "error", str(exc))
