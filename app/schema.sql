PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS owners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT UNIQUE,
    name TEXT NOT NULL,
    telegram_chat_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS drivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT UNIQUE,
    name TEXT NOT NULL,
    owner_id INTEGER,
    is_owner_driver INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES owners(id)
);

CREATE TABLE IF NOT EXISTS bank_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT UNIQUE,
    owner_id INTEGER,
    driver_id INTEGER,
    label TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES owners(id),
    FOREIGN KEY (driver_id) REFERENCES drivers(id)
);

CREATE TABLE IF NOT EXISTS trucks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT UNIQUE,
    owner_id INTEGER NOT NULL,
    plate TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES owners(id)
);

CREATE TABLE IF NOT EXISTS loads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT UNIQUE,
    driver_id INTEGER,
    truck_id INTEGER,
    load_date TEXT,
    description TEXT,
    amount_gross REAL NOT NULL,
    slv_fee_percent REAL DEFAULT 0.0,
    recife_fee_percent REAL DEFAULT 10.0,
    status TEXT DEFAULT 'open',
    week_reference TEXT,
    sheet_owner TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (driver_id) REFERENCES drivers(id),
    FOREIGN KEY (truck_id) REFERENCES trucks(id)
);

CREATE TABLE IF NOT EXISTS bank_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT UNIQUE,
    account_id INTEGER,
    txn_date TEXT NOT NULL,
    description TEXT,
    amount REAL NOT NULL,
    transaction_type TEXT DEFAULT 'credit',
    category TEXT,
    related_account_id INTEGER,
    sheet_owner TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES bank_accounts(id),
    FOREIGN KEY (related_account_id) REFERENCES bank_accounts(id)
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_transaction_id INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bank_transaction_id) REFERENCES bank_transactions(id)
);

CREATE TABLE IF NOT EXISTS bank_reconciliations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_transaction_id INTEGER NOT NULL,
    reconciliation_type TEXT NOT NULL,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER,
    truck_id INTEGER,
    bank_account_id INTEGER,
    expense_date TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT,
    category TEXT,
    cost_center TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES owners(id),
    FOREIGN KEY (truck_id) REFERENCES trucks(id),
    FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id)
);

CREATE TABLE IF NOT EXISTS ledger_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER,
    driver_id INTEGER,
    entry_date TEXT NOT NULL,
    entry_type TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES owners(id),
    FOREIGN KEY (driver_id) REFERENCES drivers(id)
);

CREATE INDEX IF NOT EXISTS idx_loads_status ON loads(status);
CREATE INDEX IF NOT EXISTS idx_bank_txn_date ON bank_transactions(txn_date);
