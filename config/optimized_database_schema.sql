-- AI-Driven Stock Trade Advisor - Optimized Database Schema
-- Lightweight SQLite schema with UIDs and optimized indexing
-- Focus: Performance, minimal storage, efficient queries

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;

-- ============================================================================
-- CORE ENTITIES (with UIDs)
-- ============================================================================

-- Users: Core user profiles with UIDs
CREATE TABLE IF NOT EXISTS users (
    uid TEXT PRIMARY KEY, -- UUID for object identification
    id INTEGER UNIQUE, -- Auto-increment for internal references
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    risk_profile TEXT CHECK(risk_profile IN ('conservative', 'moderate', 'aggressive')) DEFAULT 'moderate',
    max_position_pct REAL DEFAULT 0.1 CHECK(max_position_pct > 0 AND max_position_pct <= 1),
    stop_loss_pct REAL DEFAULT 0.05 CHECK(stop_loss_pct > 0),
    take_profit_pct REAL DEFAULT 0.15 CHECK(take_profit_pct > 0),
    created_at INTEGER DEFAULT (unixepoch()),
    updated_at INTEGER DEFAULT (unixepoch()),
    is_active INTEGER DEFAULT 1
);

-- Symbols: Market symbols with metadata
CREATE TABLE IF NOT EXISTS symbols (
    uid TEXT PRIMARY KEY,
    id INTEGER UNIQUE,
    symbol TEXT UNIQUE NOT NULL,
    name TEXT,
    sector TEXT,
    industry TEXT,
    market_cap REAL,
    is_active INTEGER DEFAULT 1,
    created_at INTEGER DEFAULT (unixepoch())
);

-- ============================================================================
-- MARKET DATA (Optimized for time-series queries)
-- ============================================================================

-- Market data: Efficient OHLCV storage with partitioning by symbol
CREATE TABLE IF NOT EXISTS market_data (
    uid TEXT PRIMARY KEY,
    id INTEGER UNIQUE,
    symbol_id INTEGER NOT NULL,
    date INTEGER NOT NULL, -- Unix timestamp for efficient range queries
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    created_at INTEGER DEFAULT (unixepoch()),
    FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);

-- Technical indicators: Calculated indicators with symbol reference
CREATE TABLE IF NOT EXISTS indicators (
    uid TEXT PRIMARY KEY,
    id INTEGER UNIQUE,
    symbol_id INTEGER NOT NULL,
    date INTEGER NOT NULL,
    indicator_type TEXT NOT NULL, -- 'sma', 'ema', 'rsi', 'macd', etc.
    value REAL NOT NULL,
    params TEXT, -- JSON string for indicator parameters
    created_at INTEGER DEFAULT (unixepoch()),
    FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);

-- ============================================================================
-- TRADING LOGIC (Core business entities)
-- ============================================================================

-- Trade signals: Generated trading signals with UIDs
CREATE TABLE IF NOT EXISTS signals (
    uid TEXT PRIMARY KEY,
    id INTEGER UNIQUE,
    user_id INTEGER NOT NULL,
    symbol_id INTEGER NOT NULL,
    signal_type TEXT CHECK(signal_type IN ('buy', 'sell', 'hold')) NOT NULL,
    risk_level TEXT CHECK(risk_level IN ('low', 'medium', 'high')) NOT NULL,
    confidence REAL CHECK(confidence >= 0 AND confidence <= 1),
    price_target REAL,
    stop_loss REAL,
    take_profit REAL,
    rationale TEXT,
    source TEXT, -- 'rule_based', 'ml_model', 'hybrid'
    created_at INTEGER DEFAULT (unixepoch()),
    expires_at INTEGER,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);

-- Trades: Executed trades with UIDs
CREATE TABLE IF NOT EXISTS trades (
    uid TEXT PRIMARY KEY,
    id INTEGER UNIQUE,
    user_id INTEGER NOT NULL,
    symbol_id INTEGER NOT NULL,
    signal_id INTEGER,
    trade_type TEXT CHECK(trade_type IN ('buy', 'sell')) NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    price REAL NOT NULL CHECK(price > 0),
    total_amount REAL NOT NULL,
    commission REAL DEFAULT 0,
    trade_date INTEGER DEFAULT (unixepoch()),
    is_paper INTEGER DEFAULT 1, -- 1=paper, 0=real
    status TEXT CHECK(status IN ('pending', 'filled', 'cancelled')) DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (symbol_id) REFERENCES symbols(id),
    FOREIGN KEY (signal_id) REFERENCES signals(id)
);

-- Positions: Current portfolio positions
CREATE TABLE IF NOT EXISTS positions (
    uid TEXT PRIMARY KEY,
    id INTEGER UNIQUE,
    user_id INTEGER NOT NULL,
    symbol_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    avg_price REAL NOT NULL,
    current_price REAL,
    market_value REAL,
    unrealized_pnl REAL,
    realized_pnl REAL DEFAULT 0,
    last_updated INTEGER DEFAULT (unixepoch()),
    UNIQUE(user_id, symbol_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);

-- ============================================================================
-- PERFORMANCE & ANALYTICS (Optimized for reporting)
-- ============================================================================

-- Performance snapshots: Daily performance metrics
CREATE TABLE IF NOT EXISTS performance (
    uid TEXT PRIMARY KEY,
    id INTEGER UNIQUE,
    user_id INTEGER NOT NULL,
    date INTEGER NOT NULL,
    portfolio_value REAL NOT NULL,
    daily_return REAL,
    cumulative_return REAL,
    sharpe_ratio REAL,
    max_drawdown REAL,
    win_rate REAL,
    profit_factor REAL,
    created_at INTEGER DEFAULT (unixepoch()),
    UNIQUE(user_id, date),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ============================================================================
-- ML MODELS (Lightweight model tracking)
-- ============================================================================

-- ML models: Trained model metadata
CREATE TABLE IF NOT EXISTS models (
    uid TEXT PRIMARY KEY,
    id INTEGER UNIQUE,
    name TEXT NOT NULL,
    model_type TEXT NOT NULL, -- 'classification', 'regression', 'ensemble'
    version TEXT NOT NULL,
    file_path TEXT NOT NULL,
    accuracy REAL,
    precision REAL,
    recall REAL,
    f1_score REAL,
    is_active INTEGER DEFAULT 0,
    created_at INTEGER DEFAULT (unixepoch()),
    updated_at INTEGER DEFAULT (unixepoch())
);

-- Model predictions: Stored predictions with UIDs
CREATE TABLE IF NOT EXISTS predictions (
    uid TEXT PRIMARY KEY,
    id INTEGER UNIQUE,
    model_id INTEGER NOT NULL,
    symbol_id INTEGER NOT NULL,
    prediction_date INTEGER NOT NULL,
    predicted_value REAL,
    confidence REAL,
    created_at INTEGER DEFAULT (unixepoch()),
    FOREIGN KEY (model_id) REFERENCES models(id),
    FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);

-- ============================================================================
-- SYSTEM & AUDIT (Minimal but essential)
-- ============================================================================

-- Audit log: Essential system activities
CREATE TABLE IF NOT EXISTS audit_log (
    uid TEXT PRIMARY KEY,
    id INTEGER UNIQUE,
    user_id INTEGER,
    action TEXT NOT NULL,
    entity_type TEXT, -- 'user', 'trade', 'signal', etc.
    entity_uid TEXT, -- Reference to the affected entity
    details TEXT, -- JSON string for additional details
    created_at INTEGER DEFAULT (unixepoch()),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- API usage: Rate limiting and monitoring
CREATE TABLE IF NOT EXISTS api_usage (
    uid TEXT PRIMARY KEY,
    id INTEGER UNIQUE,
    api_name TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    response_code INTEGER,
    response_time_ms INTEGER,
    created_at INTEGER DEFAULT (unixepoch())
);

-- ============================================================================
-- OPTIMIZED INDEXES (Performance-focused)
-- ============================================================================

-- Market data indexes (most critical for performance)
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_date ON market_data(symbol_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_market_data_date ON market_data(date DESC);
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_date_range ON market_data(symbol_id, date DESC) WHERE date > 0;

-- Technical indicators indexes
CREATE INDEX IF NOT EXISTS idx_indicators_symbol_type_date ON indicators(symbol_id, indicator_type, date DESC);
CREATE INDEX IF NOT EXISTS idx_indicators_type_date ON indicators(indicator_type, date DESC);

-- Trading indexes
CREATE INDEX IF NOT EXISTS idx_signals_user_active ON signals(user_id, is_active) WHERE is_active = 1;
CREATE INDEX IF NOT EXISTS idx_signals_symbol_date ON signals(symbol_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trades_user_date ON trades(user_id, trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_trades_symbol_date ON trades(symbol_id, trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_positions_user ON positions(user_id);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_performance_user_date ON performance(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_performance_date ON performance(date DESC);

-- ML model indexes
CREATE INDEX IF NOT EXISTS idx_predictions_model_symbol ON predictions(model_id, symbol_id);
CREATE INDEX IF NOT EXISTS idx_predictions_symbol_date ON predictions(symbol_id, prediction_date DESC);

-- Audit and API indexes
CREATE INDEX IF NOT EXISTS idx_audit_user_date ON audit_log(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_uid);
CREATE INDEX IF NOT EXISTS idx_api_usage_name_date ON api_usage(api_name, created_at DESC);

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Default user
INSERT OR IGNORE INTO users (uid, id, username, email, risk_profile) 
VALUES ('user_default_001', 1, 'default_user', 'default@example.com', 'moderate');

-- Common symbols
INSERT OR IGNORE INTO symbols (uid, id, symbol, name, sector) VALUES
('sym_aapl_001', 1, 'AAPL', 'Apple Inc.', 'Technology'),
('sym_msft_001', 2, 'MSFT', 'Microsoft Corporation', 'Technology'),
('sym_googl_001', 3, 'GOOGL', 'Alphabet Inc.', 'Communication Services'),
('sym_amzn_001', 4, 'AMZN', 'Amazon.com Inc.', 'Consumer Cyclical'),
('sym_tsla_001', 5, 'TSLA', 'Tesla Inc.', 'Consumer Cyclical');

-- Default model
INSERT OR IGNORE INTO models (uid, id, name, model_type, version, file_path, is_active)
VALUES ('model_default_001', 1, 'default_classifier', 'classification', '1.0.0', 'models/default_classifier.pkl', 1);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Current positions with symbol info
CREATE VIEW IF NOT EXISTS v_positions AS
SELECT 
    p.uid,
    p.user_id,
    s.symbol,
    s.name as company_name,
    p.quantity,
    p.avg_price,
    p.current_price,
    p.market_value,
    p.unrealized_pnl,
    p.realized_pnl,
    p.last_updated
FROM positions p
JOIN symbols s ON p.symbol_id = s.id
WHERE p.quantity > 0;

-- Recent signals with symbol info
CREATE VIEW IF NOT EXISTS v_recent_signals AS
SELECT 
    sig.uid,
    sig.user_id,
    s.symbol,
    sig.signal_type,
    sig.risk_level,
    sig.confidence,
    sig.price_target,
    sig.created_at
FROM signals sig
JOIN symbols s ON sig.symbol_id = s.id
WHERE sig.is_active = 1
ORDER BY sig.created_at DESC;

-- Portfolio performance summary
CREATE VIEW IF NOT EXISTS v_portfolio_summary AS
SELECT 
    u.username,
    COUNT(p.uid) as total_positions,
    SUM(p.market_value) as total_value,
    SUM(p.unrealized_pnl) as total_unrealized_pnl,
    SUM(p.realized_pnl) as total_realized_pnl
FROM users u
LEFT JOIN positions p ON u.id = p.user_id
GROUP BY u.id, u.username; 