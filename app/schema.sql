CREATE TABLE IF NOT EXISTS owners (
    id SERIAL PRIMARY KEY,
    external_id TEXT UNIQUE,
    name TEXT NOT NULL,
    telegram_chat_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS drivers (
    id SERIAL PRIMARY KEY,
    external_id TEXT UNIQUE,
    name TEXT NOT NULL,
    owner_id INTEGER,
    is_owner_driver INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES owners(id)
);

CREATE TABLE IF NOT EXISTS bank_accounts (
    id SERIAL PRIMARY KEY,
    external_id TEXT UNIQUE,
    owner_id INTEGER,
    driver_id INTEGER,
    label TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES owners(id),
    FOREIGN KEY (driver_id) REFERENCES drivers(id)
);

CREATE TABLE IF NOT EXISTS trucks (
    id SERIAL PRIMARY KEY,
    external_id TEXT UNIQUE,
    owner_id INTEGER NOT NULL,
    plate TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES owners(id)
);

CREATE TABLE IF NOT EXISTS loads (
    id SERIAL PRIMARY KEY,
    external_id TEXT UNIQUE,
    driver_id INTEGER,
    truck_id INTEGER,
    load_date DATE,
    description TEXT,
    amount_gross REAL NOT NULL,
    slv_fee_percent REAL DEFAULT 0.0 CHECK (slv_fee_percent >= 0 AND slv_fee_percent <= 100),
    recife_fee_percent REAL DEFAULT 10.0 CHECK (recife_fee_percent >= 0 AND recife_fee_percent <= 100),
    status TEXT DEFAULT 'open',
    week_reference TEXT,
    sheet_owner TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (driver_id) REFERENCES drivers(id),
    FOREIGN KEY (truck_id) REFERENCES trucks(id)
);

CREATE TABLE IF NOT EXISTS bank_transactions (
    id SERIAL PRIMARY KEY,
    external_id TEXT UNIQUE,
    account_id INTEGER,
    txn_date DATE NOT NULL,
    description TEXT,
    amount REAL NOT NULL,
    transaction_type TEXT DEFAULT 'credit' CHECK (transaction_type IN ('credit', 'debit', 'transfer')),
    category TEXT,
    related_account_id INTEGER,
    sheet_owner TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES bank_accounts(id),
    FOREIGN KEY (related_account_id) REFERENCES bank_accounts(id)
);

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    bank_transaction_id INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bank_transaction_id) REFERENCES bank_transactions(id)
);

CREATE TABLE IF NOT EXISTS bank_reconciliations (
    id SERIAL PRIMARY KEY,
    bank_transaction_id INTEGER NOT NULL,
    reconciliation_type TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bank_transaction_id) REFERENCES bank_transactions(id)
);

CREATE TABLE IF NOT EXISTS payment_loads (
    payment_id INTEGER NOT NULL,
    load_id INTEGER NOT NULL,
    PRIMARY KEY (payment_id, load_id),
    FOREIGN KEY (payment_id) REFERENCES payments(id),
    FOREIGN KEY (load_id) REFERENCES loads(id)
);

CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER,
    truck_id INTEGER,
    bank_account_id INTEGER,
    expense_date DATE NOT NULL,
    amount REAL NOT NULL,
    description TEXT,
    category TEXT,
    cost_center TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES owners(id),
    FOREIGN KEY (truck_id) REFERENCES trucks(id),
    FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id)
);

CREATE TABLE IF NOT EXISTS ledger_entries (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER,
    driver_id INTEGER,
    entry_date DATE NOT NULL,
    entry_type TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES owners(id),
    FOREIGN KEY (driver_id) REFERENCES drivers(id)
);

CREATE TABLE IF NOT EXISTS authorized_telegram_users (
    id SERIAL PRIMARY KEY,
    chat_id TEXT UNIQUE NOT NULL,
    username TEXT,
    role TEXT NOT NULL DEFAULT 'operator' CHECK (role IN ('admin', 'operator', 'viewer')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    chat_id TEXT,
    username TEXT,
    command TEXT,
    payload TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS summary_subscriptions (
    chat_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES authorized_telegram_users(chat_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_loads_status ON loads(status);
CREATE INDEX IF NOT EXISTS idx_loads_week_reference ON loads(week_reference);
CREATE INDEX IF NOT EXISTS idx_bank_txn_date ON bank_transactions(txn_date);
CREATE INDEX IF NOT EXISTS idx_expenses_owner_id ON expenses(owner_id);
CREATE INDEX IF NOT EXISTS idx_ledger_owner_driver_date ON ledger_entries(owner_id, driver_id, entry_date);
CREATE INDEX IF NOT EXISTS idx_summary_subscriptions_created_at ON summary_subscriptions(created_at);
