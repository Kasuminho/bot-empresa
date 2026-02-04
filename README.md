# Bot Empresa - Controle de Loads e Conciliação

Este repositório inicia o sistema de controle financeiro para motoristas, donos de truck e conciliação bancária.

## Como rodar localmente

### Variáveis de ambiente (.env)

Crie um arquivo `.env` (há um exemplo em `.env.example`) e configure:

```
BOT_TELEGRAM_TOKEN=seu_token_do_bot
BOT_TELEGRAM_CHAT_ID=chat_id_destino
BOT_EMPRESA_DB_PATH=/workspace/bot-empresa/data/bot_empresa.db
```

> O `.env` é carregado automaticamente pelo backend via `python-dotenv`.

### Como pegar o token do bot (Telegram)

1. Abra o Telegram e fale com o `@BotFather`.
2. Envie `/newbot` e siga o passo a passo.
3. Ao final, o BotFather retorna o **token**. Cole esse valor no `.env` em `BOT_TELEGRAM_TOKEN`.
4. Para descobrir o `BOT_TELEGRAM_CHAT_ID`, mande uma mensagem para o bot e use um método rápido:
   - Abra `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates` no navegador.
   - Encontre o campo `"chat":{"id":...}` e use esse número.

### Como o bot recebe CSV

Os CSVs entram via CLI. Basta salvar o arquivo (ex: `data/owners.csv`) e executar o comando
de importação correspondente. O sistema faz *upsert* por `*_id`.

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

## Cadastros manuais (sem CSV)

Use a CLI para cadastrar entidades diretamente:

```bash
python -m app.cli add-owner --owner-id OWNER_01 --name "João" --telegram-chat-id "123456"
python -m app.cli add-driver --driver-id DRIVER_01 --name "Carlos" --owner-id OWNER_01 --is-owner-driver
python -m app.cli add-truck --truck-id TRUCK_01 --owner-id OWNER_01 --plate "ABC1234"
python -m app.cli add-account --account-id ACC_01 --label "Conta Principal" --owner-id OWNER_01
python -m app.cli add-load --load-id LOAD_01 --driver-id DRIVER_01 --truck-id TRUCK_01 --load-date 2024-07-01 --amount-gross 1500 --description "Load semanal"
python -m app.cli add-expense --owner-id OWNER_01 --truck-id TRUCK_01 --account-id ACC_01 --expense-date 2024-07-02 --amount 200 --description "ELD"
python -m app.cli add-bank-transaction --transaction-id TXN_01 --account-id ACC_01 --txn-date 2024-07-03 --amount 1500 --transaction-type credit --description "Pagamento"
```

> Também é possível enviar mensagem para o Telegram sem passar token/ID na linha de comando,
> desde que o `.env` esteja configurado.

## Próximos passos planejados

- Rotina de comissão semanal e conta-corrente por motorista/dono.
- Lançamento de despesas e cálculo automático de dispatcher fee.
- Integração direta com bot do Telegram para alertas de provisão e saldo.
