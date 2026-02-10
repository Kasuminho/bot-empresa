# Bot Empresa - Controle de Loads e Conciliação

Este repositório inicia o sistema de controle financeiro para motoristas, donos de truck e conciliação bancária.

## Como rodar localmente

### Variáveis de ambiente (.env)

Crie um arquivo `.env` (há um exemplo em `.env.example`) e configure:

```
BOT_TELEGRAM_TOKEN=seu_token_do_bot
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/bot_empresa
BOT_TELEGRAM_WEBHOOK_SECRET=segredo_opcional
BOT_TELEGRAM_ADMIN_CHAT_IDS=123456789
BOT_SUMMARY_SCHEDULE_ENABLED=0
BOT_SUMMARY_SCHEDULE_INTERVAL_MINUTES=60
```

> O `.env` é carregado automaticamente pelo backend ao iniciar a aplicação.

### Como pegar o token do bot (Telegram)

1. Abra o Telegram e fale com o `@BotFather`.
2. Envie `/newbot` e siga o passo a passo.
3. Ao final, o BotFather retorna o **token**. Cole esse valor no `.env` em `BOT_TELEGRAM_TOKEN`.

### Como usar o bot pelo Telegram (UI)

1. Suba o servidor localmente ou em produção (o webhook precisa acessar `/telegram/webhook`).
2. Configure o webhook do Telegram (use o mesmo token do `.env`):
   ```bash
   curl -X POST "https://api.telegram.org/bot<SEU_TOKEN>/setWebhook" \\
     -d "url=https://SEU_DOMINIO/telegram/webhook" \\
     -d "secret_token=SEU_SEGREDO_OPCIONAL"
   ```
3. No Telegram, envie `/start` para ver os comandos.

Exemplos no chat:
```
/add_owner owner_id=OWNER_01 name="João" telegram_chat_id=123456
/add_driver driver_id=DRIVER_01 name="Carlos" owner_id=OWNER_01 is_owner_driver=1
/add_truck truck_id=TRUCK_01 owner_id=OWNER_01 plate=ABC1234
/add_account account_id=ACC_01 label="Conta Principal" owner_id=OWNER_01
/add_load load_id=LOAD_01 driver_id=DRIVER_01 truck_id=TRUCK_01 load_date=2024-07-01 amount_gross=1500 description="Load semanal"
/add_expense owner_id=OWNER_01 truck_id=TRUCK_01 account_id=ACC_01 expense_date=2024-07-02 amount=200 description="ELD"
/add_bank_transaction transaction_id=TXN_01 account_id=ACC_01 txn_date=2024-07-03 amount=1500 transaction_type=credit description="Pagamento"
/summary
/close_week week_reference=2024-W27
/ledger owner_id=OWNER_01 limit=10
/open_loads owner_id=OWNER_01
/balance owner_id=OWNER_01
/suggest_reconcile transaction_id=TXN_01
/subscribe_summary
```

Importação de CSV pelo Telegram:

1. Envie o arquivo CSV para o bot.
2. Use a **legenda** do arquivo para passar o comando de importação.

Exemplos de legenda:
```
/import_owners
/import_drivers
/import_trucks
/import_accounts
/import_loads sheet_owner="Pai"
/import_bank sheet_owner="Eu"
/import_expenses
/import_car_loads truck_id=TRUCK_01 sheet_owner="Pai"
```

> Se você configurar `BOT_TELEGRAM_WEBHOOK_SECRET`, o Telegram enviará o cabeçalho
> `X-Telegram-Bot-Api-Secret-Token`, e o backend valida automaticamente.

### Lançamento de despesas e dispatcher fee automático

Ao cadastrar ou importar loads, o sistema gera automaticamente uma despesa
de dispatcher fee com base em `recife_fee_percent`. A despesa é criada apenas
uma vez por load e fica registrada em `expenses` com a descrição
`Dispatcher fee load <load_id>`.

### Comissão semanal e conta-corrente

Use `/close_week` para fechar uma semana e gerar lançamentos em `ledger_entries`.
Use `/ledger` para consultar os últimos lançamentos por dono ou motorista.
Use `/open_loads` e `/balance` para visualizar valores em aberto e quanto há a receber/pagar.

### Segurança e acesso

- Apenas usuários autorizados conseguem executar comandos sensíveis.
- Configure os admins iniciais em `BOT_TELEGRAM_ADMIN_CHAT_IDS`.
- Admin pode autorizar novos usuários via:
  - `/authorize chat_id=123456 role=operator`

### Confirmação de ações críticas

- `/add_load` e `/close_week` entram em confirmação antes de gravar.
- Use `/confirm` para confirmar ou `/cancel` para abortar.

### Auditoria

Todas as ações do bot são registradas em `audit_log` (comando, payload, status e erro).

### Import CSV com validação e dry-run

- O bot valida cabeçalhos mínimos por tipo de importação.
- Para validar sem gravar, use `dry_run=1` na legenda, por exemplo:
  - `/import_loads sheet_owner="Pai" dry_run=1`

### Sugestão de conciliação

Use `/suggest_reconcile transaction_id=TXN_01` para receber sugestões de loads
pendentes por proximidade de valor e data.

### Resumo automático agendado

- Ative com `BOT_SUMMARY_SCHEDULE_ENABLED=1`.
- Intervalo em minutos por `BOT_SUMMARY_SCHEDULE_INTERVAL_MINUTES`.
- Usuários inscritos recebem resumo automático (`/subscribe_summary`).

### Passos para subir o servidor (PostgreSQL)

1. Garanta um PostgreSQL ativo e crie o banco `bot_empresa`.
2. Configure `DATABASE_URL` no `.env`.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.cli init-db
uvicorn app.server:app --reload --port 8000
```

Acesse `http://localhost:8000` para a tela de conciliação.

### Estrutura MVC

- **Controllers**: rotas e fluxo HTTP/Telegram em `app/controllers` (APIRouter).
- **Services**: casos de uso e orquestração em `app/services` (ex: `TelegramService`, `WebService`, `FinanceService`, `RegistrationService`).
- **Repositories**: acesso a dados em `app/repositories` (PostgreSQL).
- **Models**: DTOs/estruturas de dados em `app/models`.
- **Views**: templates em `app/templates`.
- **Facades compatíveis**: módulos `app/finance.py` e `app/registrations.py` preservam API pública delegando para services.
