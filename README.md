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

### Troubleshooting do webhook (erro `Connection refused`)

Se no `getWebhookInfo` aparecer `last_error_message: "Connection refused"`, o problema é de
**conectividade de rede/porta**, não de comando do bot. Isso normalmente significa que o Telegram
não conseguiu abrir conexão HTTPS com seu domínio.

Checklist recomendado:

1. Verifique se a aplicação está ativa (ex.: `uvicorn app.server:app --host 0.0.0.0 --port 8000`).
2. Garanta um reverse proxy (Nginx/Caddy/Traefik) escutando em **443** e encaminhando para a porta
   interna da aplicação (ex.: 8000).
3. Confirme que a porta 443 está liberada no firewall/NAT do servidor.
4. Valide se o DNS do domínio aponta para o IP público correto da máquina.
5. Após corrigir, rode novamente o `setWebhook`.

Exemplo mínimo de teste local no servidor:

```bash
curl -vk https://localhost/telegram/webhook
```

Se esse comando retornar `Connection refused`, então não existe serviço HTTPS escutando em 443 no host.
Nesse caso, suba/corrija o reverse proxy antes de tentar novamente o webhook.


### Exemplo prático de reverse proxy com Nginx (HTTPS -> Uvicorn 8000)

1. Suba o backend na porta interna 8000:

```bash
uvicorn app.server:app --host 0.0.0.0 --port 8000
```

2. Crie o arquivo do site no Nginx (ex.: `/etc/nginx/sites-available/bot-empresa`):

```nginx
server {
    listen 80;
    server_name innoshift.ddns.net;

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name innoshift.ddns.net;

    ssl_certificate     /etc/letsencrypt/live/innoshift.ddns.net/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/innoshift.ddns.net/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. Ative o site e recarregue o Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/bot-empresa /etc/nginx/sites-enabled/bot-empresa
sudo nginx -t
sudo systemctl reload nginx
```

4. (Se necessário) abra firewall:

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

5. Teste local e externo:

```bash
curl -vk https://localhost/telegram/webhook
curl -vk https://innoshift.ddns.net/telegram/webhook
```

6. Reaplique o webhook do Telegram:

```bash
curl -X POST "https://api.telegram.org/bot<SEU_TOKEN>/setWebhook" \
  -d "url=https://innoshift.ddns.net/telegram/webhook" \
  -d "secret_token=<SEU_SEGREDO_OPCIONAL>"
```

> Dica: para emitir certificado TLS, você pode usar `certbot --nginx -d innoshift.ddns.net`.


### Windows 10 (jeito mais simples): Cloudflare Tunnel (sem Nginx)

Se você está no Windows 10 e não quer configurar reverse proxy manual, use **Cloudflare Tunnel**.
Ele publica seu `localhost:8000` em HTTPS automaticamente.

1. Suba o backend:

```powershell
uvicorn app.server:app --host 0.0.0.0 --port 8000
```

2. Instale o `cloudflared` no Windows:
   - Via winget:

```powershell
winget install --id Cloudflare.cloudflared
```

3. Em outro terminal, abra um túnel para a porta 8000:

```powershell
cloudflared tunnel --url http://localhost:8000
```

4. O comando vai mostrar uma URL `https://....trycloudflare.com`.
   Configure essa URL no webhook:

```powershell
curl -X POST "https://api.telegram.org/bot<SEU_TOKEN>/setWebhook" `
  -d "url=https://SEU_SUBDOMINIO.trycloudflare.com/telegram/webhook" `
  -d "secret_token=<SEU_SEGREDO_OPCIONAL>"
```

5. Verifique status:

```powershell
curl "https://api.telegram.org/bot<SEU_TOKEN>/getWebhookInfo"
```

> Observação: URL `trycloudflare.com` pode mudar quando reiniciar o túnel. Para produção estável,
> use domínio próprio no Cloudflare com túnel nomeado.

### Windows 10 (opção local com Caddy)

Se preferir rodar tudo local com reverse proxy no Windows, Caddy é o caminho mais simples.

1. Suba o backend na 8000:

```powershell
uvicorn app.server:app --host 0.0.0.0 --port 8000
```

2. Instale o Caddy:

```powershell
winget install --id CaddyServer.Caddy
```

3. Crie um arquivo `Caddyfile` no diretório do projeto:

```caddyfile
innoshift.ddns.net {
    reverse_proxy 127.0.0.1:8000
}
```

4. Execute o Caddy como administrador:

```powershell
caddy run
```

5. Libere a porta 443 no Firewall do Windows e no roteador (port forwarding) para o IP da máquina.

6. Teste:

```powershell
curl -vk https://innoshift.ddns.net/telegram/webhook
```

Se responder sem `Connection refused`, reaplique o `setWebhook`.



### Webhook retorna 200, mas `/start` não responde (checklist)

Se o endpoint está no ar mas o bot não processa mensagens, valide nesta ordem:

1. **Webhook secret igual ao configurado no Telegram**
   - Se `BOT_TELEGRAM_WEBHOOK_SECRET` estiver definido no `.env`, você precisa enviar o mesmo valor no `setWebhook` (`secret_token`).
   - Se o secret estiver diferente, o backend rejeita a chamada com **403** e a mensagem não é processada.

2. **Token correto do bot**
   - Confirme `BOT_TELEGRAM_TOKEN` no `.env` e compare com o token usado no `setWebhook`.

3. **Limpe webhook antigo e configure de novo**

```bash
curl -X POST "https://api.telegram.org/bot<SEU_TOKEN>/deleteWebhook?drop_pending_updates=true"
curl -X POST "https://api.telegram.org/bot<SEU_TOKEN>/setWebhook" \
  -d "url=https://SEU_DOMINIO/telegram/webhook" \
  -d "secret_token=<SEU_SEGREDO_OPCIONAL>"
```

4. **Cheque status do webhook**

```bash
curl "https://api.telegram.org/bot<SEU_TOKEN>/getWebhookInfo"
```

   - `last_error_message` deve ficar vazio.
   - `pending_update_count` deve diminuir com o tempo.

5. **Publique comandos no menu do Telegram (opcional, mas recomendado)**

```bash
curl -X POST "https://api.telegram.org/bot<SEU_TOKEN>/setMyCommands" \
  -H "Content-Type: application/json" \
  -d '{"commands":[{"command":"start","description":"Inicia o bot"},{"command":"help","description":"Lista comandos"},{"command":"summary","description":"Resumo financeiro"}]}'
```

6. **Teste em chat privado com o bot**
   - Abra conversa direta com o bot, clique em **Start** e depois envie `/start` manualmente.



### Fluxo simples (sem inventar IDs manualmente)

Agora os comandos de cadastro aceitam IDs opcionais. Se você não enviar `owner_id`, `driver_id`,
`truck_id`, `account_id`, `load_id` ou `transaction_id`, o bot gera automaticamente e te devolve no retorno.

Exemplo real de uso no dia a dia:

```text
/add_owner name="João"
/add_driver name="Carlos" owner_id=OWNER_XXXXXXXX
/add_truck owner_id=OWNER_XXXXXXXX plate=ABC1234
/add_account label="Conta Principal" owner_id=OWNER_XXXXXXXX
/add_load amount_gross=1500 driver_id=DRIVER_XXXXXXXX truck_id=TRUCK_XXXXXXXX load_date=2024-07-01
/add_bank_transaction txn_date=2024-07-03 amount=1500 account_id=ACC_XXXXXXXX description="Pagamento"
```

> Dica: cadastre primeiro o dono com `/add_owner name="..."`, copie o `owner_id` retornado e use nos próximos passos.

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
