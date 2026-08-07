-- Publiusly identity mirror (users + user_credentials) + trade MVP tables.
-- On production publiusly-db: CREATE IF NOT EXISTS is a no-op for existing
-- identity tables and only adds sessions / app_memberships / trade_*.

PRAGMA foreign_keys = ON;

-- Match production Publiusly schema (services/api/src/auth/schema.sql)
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  email_verified INTEGER NOT NULL DEFAULT 0,
  display_name TEXT,
  role TEXT NOT NULL DEFAULT 'user',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS user_credentials (
  user_id TEXT PRIMARY KEY,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Trade-owned session cookies (separate from Publiusly refresh_tokens / JWT)
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY NOT NULL,
  user_id TEXT NOT NULL,
  token_hash TEXT NOT NULL UNIQUE,
  expires_at INTEGER NOT NULL,
  created_at INTEGER NOT NULL DEFAULT (unixepoch()),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS app_memberships (
  id TEXT PRIMARY KEY NOT NULL,
  user_id TEXT NOT NULL,
  app_id TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'trader',
  permissions_json TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'invited', 'revoked')),
  created_at INTEGER NOT NULL DEFAULT (unixepoch()),
  updated_at INTEGER NOT NULL DEFAULT (unixepoch()),
  UNIQUE (user_id, app_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS trade_profiles (
  user_id TEXT PRIMARY KEY NOT NULL,
  risk_tolerance TEXT NOT NULL DEFAULT 'moderate'
    CHECK (risk_tolerance IN ('conservative', 'moderate', 'aggressive')),
  investment_goals TEXT,
  max_position_pct REAL NOT NULL DEFAULT 0.1,
  stop_loss_pct REAL NOT NULL DEFAULT 0.05,
  take_profit_pct REAL NOT NULL DEFAULT 0.15,
  portfolio_value REAL NOT NULL DEFAULT 100000,
  created_at INTEGER NOT NULL DEFAULT (unixepoch()),
  updated_at INTEGER NOT NULL DEFAULT (unixepoch()),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS trade_watchlists (
  id TEXT PRIMARY KEY NOT NULL,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  is_default INTEGER NOT NULL DEFAULT 0,
  created_at INTEGER NOT NULL DEFAULT (unixepoch()),
  updated_at INTEGER NOT NULL DEFAULT (unixepoch()),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS trade_watchlist_symbols (
  id TEXT PRIMARY KEY NOT NULL,
  watchlist_id TEXT NOT NULL,
  symbol TEXT NOT NULL COLLATE NOCASE,
  notes TEXT,
  added_at INTEGER NOT NULL DEFAULT (unixepoch()),
  UNIQUE (watchlist_id, symbol),
  FOREIGN KEY (watchlist_id) REFERENCES trade_watchlists(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS trade_orders (
  id TEXT PRIMARY KEY NOT NULL,
  user_id TEXT NOT NULL,
  symbol TEXT NOT NULL COLLATE NOCASE,
  side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
  order_type TEXT NOT NULL DEFAULT 'market' CHECK (order_type IN ('market', 'limit')),
  quantity REAL NOT NULL,
  limit_price REAL,
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'submitted', 'filled', 'cancelled', 'rejected')),
  broker TEXT NOT NULL DEFAULT 'mock',
  broker_order_id TEXT,
  filled_price REAL,
  filled_at INTEGER,
  created_at INTEGER NOT NULL DEFAULT (unixepoch()),
  updated_at INTEGER NOT NULL DEFAULT (unixepoch()),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS trade_positions (
  id TEXT PRIMARY KEY NOT NULL,
  user_id TEXT NOT NULL,
  symbol TEXT NOT NULL COLLATE NOCASE,
  quantity REAL NOT NULL,
  avg_entry_price REAL NOT NULL,
  current_price REAL,
  updated_at INTEGER NOT NULL DEFAULT (unixepoch()),
  UNIQUE (user_id, symbol),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_memberships_user_app ON app_memberships(user_id, app_id);
CREATE INDEX IF NOT EXISTS idx_watchlists_user ON trade_watchlists(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_user ON trade_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_user ON trade_positions(user_id);
