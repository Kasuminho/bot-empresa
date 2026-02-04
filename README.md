# Bot Empresa - Controle de Loads e Conciliação

Este repositório inicia o sistema de controle financeiro para motoristas, donos de truck e conciliação bancária.

## Como rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.cli init-db
uvicorn app.server:app --reload --port 8000
```

Acesse `http://localhost:8000` para a tela de conciliação.

## Importações (CSV)

A planilha deve conter o histórico completo. O sistema faz *upsert* pelo campo `*_id`.

### Owners (`import-owners`)

Campos:
- `owner_id` (string, único)
- `name`
- `telegram_chat_id` (opcional)

### Drivers (`import-drivers`)

Campos:
- `driver_id` (string, único)
- `name`
- `owner_id` (referência para `owner_id`)
- `is_owner_driver` (`1` para motorista ser dono do truck)

### Trucks (`import-trucks`)

Campos:
- `truck_id` (string, único)
- `owner_id`
- `plate`

### Loads (`import-loads`)

Campos:
- `load_id` (string, único)
- `driver_id`
- `truck_id`
- `load_date` (YYYY-MM-DD ou DD/MM/YYYY)
- `description`
- `amount_gross`
- `slv_fee_percent` (opcional)
- `recife_fee_percent` (opcional, default 10%)
- `status` (default `open`)
- `week_reference`

### Loads de carros (`import-car-loads`)

Usa o CSV no formato enviado (carros/transportes) e escolhe o caminhão via CLI.

Campos esperados no CSV:
- `Order ID`
- `Pickup Date`
- `Delivery Date`
- `RATE`
- `DISPATCHER FEE` (opcional, default 10%)
- `EMPRESA`

Uso:
```bash
python -m app.cli import-car-loads data/car_loads.csv --truck-id TRUCK_01 --sheet-owner "Pai"
```

### Contas bancárias (`import-accounts`)

Campos:
- `account_id` (string, único)
- `label` (ex: "Conta principal", "Conta motorista A")
- `owner_id` (opcional)
- `driver_id` (opcional, quando a conta for usada por motorista)

### Banco (`import-bank`)

Campos:
- `transaction_id` (string, único)
- `account_id` (referência para `account_id`)
- `txn_date` (YYYY-MM-DD ou DD/MM/YYYY)
- `description`
- `amount`
- `transaction_type` (`credit`, `debit`, `transfer`)
- `category` (opcional)
- `related_account_id` (opcional, para transferências internas)

### Despesas (`import-expenses`)

Campos:
- `owner_id`
- `truck_id`
- `account_id` (conta usada no pagamento)
- `expense_date` (YYYY-MM-DD ou DD/MM/YYYY)
- `amount`
- `description`
- `category`
- `cost_center` (ex: Seguro, ELD, Manutenção)

## CLI rápida

```bash
python -m app.cli import-owners data/owners.csv
python -m app.cli import-drivers data/drivers.csv
python -m app.cli import-trucks data/trucks.csv
python -m app.cli import-accounts data/accounts.csv
python -m app.cli import-loads data/loads.csv --sheet-owner "Pai"
python -m app.cli import-bank data/bank.csv --sheet-owner "Eu"
python -m app.cli import-expenses data/expenses.csv
```

## Telegram

```bash
python -m app.cli send-telegram --token "TOKEN" --chat-id "CHAT" --text "Resumo diário"
```

## Próximos passos planejados

- Rotina de comissão semanal e conta-corrente por motorista/dono.
- Lançamento de despesas e cálculo automático de dispatcher fee.
- Integração direta com bot do Telegram para alertas de provisão e saldo.
