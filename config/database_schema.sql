-- AI-Driven Stock Trade Advisor Database Schema
-- SQLite database schema for local data storage
-- This file defines all tables and their relationships

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Users table - Store user profiles and preferences
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    risk_tolerance TEXT CHECK(risk_tolerance IN ('low', 'medium', 'high')) DEFAULT 'medium',
    investment_goals TEXT,
    max_position_size REAL DEFAULT 0.1,
    stop_loss_percentage REAL DEFAULT 0.05,
    take_profit_percentage REAL DEFAULT 0.15,
    is_active BOOLEAN DEFAULT 1
);

-- Market data cache table - Store historical market data
CREATE TABLE IF NOT EXISTS market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    adjusted_close REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);

-- Technical indicators table - Store calculated technical indicators
CREATE TABLE IF NOT EXISTS technical_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    indicator_name TEXT NOT NULL,
    indicator_value REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date, indicator_name)
);

-- Trade suggestions table - Store generated trade recommendations
CREATE TABLE IF NOT EXISTS trade_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    suggestion_type TEXT CHECK(suggestion_type IN ('buy', 'sell', 'hold')) NOT NULL,
    risk_level TEXT CHECK(risk_level IN ('low', 'medium', 'high')) NOT NULL,
    confidence_score REAL CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
    price_target REAL,
    stop_loss REAL,
    take_profit REAL,
    rationale TEXT,
    technical_signals TEXT, -- JSON string of technical indicators
    fundamental_signals TEXT, -- JSON string of fundamental data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_executed BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Trade history table - Store executed trades
CREATE TABLE IF NOT EXISTS trade_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    trade_type TEXT CHECK(trade_type IN ('buy', 'sell')) NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    total_amount REAL NOT NULL,
    commission REAL DEFAULT 0.0,
    trade_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    suggestion_id INTEGER,
    paper_trade BOOLEAN DEFAULT 1, -- 1 for paper trading, 0 for real trading
    status TEXT CHECK(status IN ('pending', 'filled', 'cancelled', 'rejected')) DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (suggestion_id) REFERENCES trade_suggestions(id)
);

-- Portfolio positions table - Track current positions
CREATE TABLE IF NOT EXISTS portfolio_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    average_price REAL NOT NULL,
    current_price REAL,
    total_value REAL,
    unrealized_pnl REAL,
    realized_pnl REAL DEFAULT 0.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Performance metrics table - Store calculated performance metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date DATE NOT NULL,
    total_value REAL,
    daily_return REAL,
    cumulative_return REAL,
    sharpe_ratio REAL,
    max_drawdown REAL,
    win_rate REAL,
    profit_factor REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Machine learning models table - Store trained models
CREATE TABLE IF NOT EXISTS ml_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    model_type TEXT NOT NULL,
    model_version TEXT NOT NULL,
    model_path TEXT NOT NULL,
    training_data_start DATE,
    training_data_end DATE,
    accuracy_score REAL,
    precision_score REAL,
    recall_score REAL,
    f1_score REAL,
    is_active BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model predictions table - Store model predictions
CREATE TABLE IF NOT EXISTS model_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    prediction_date DATE NOT NULL,
    prediction_value REAL,
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES ml_models(id)
);

-- Audit log table - Track all system activities
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    table_name TEXT,
    record_id INTEGER,
    old_values TEXT, -- JSON string of old values
    new_values TEXT, -- JSON string of new values
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Risk disclosures table - Track user acknowledgments
CREATE TABLE IF NOT EXISTS risk_disclosures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    disclosure_type TEXT NOT NULL,
    disclosure_version TEXT NOT NULL,
    acknowledged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- API usage log table - Track API calls for rate limiting
CREATE TABLE IF NOT EXISTS api_usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_name TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    response_code INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_date ON market_data(symbol, date);
CREATE INDEX IF NOT EXISTS idx_technical_indicators_symbol_date ON technical_indicators(symbol, date);
CREATE INDEX IF NOT EXISTS idx_trade_suggestions_user_created ON trade_suggestions(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_trade_history_user_date ON trade_history(user_id, trade_date);
CREATE INDEX IF NOT EXISTS idx_portfolio_positions_user ON portfolio_positions(user_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_user_date ON performance_metrics(user_id, date);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_created ON audit_log(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_log_api_created ON api_usage_log(api_name, created_at);

-- Insert default user if none exists
INSERT OR IGNORE INTO users (id, username, email, risk_tolerance) 
VALUES (1, 'default_user', 'default@example.com', 'medium');

-- Insert default risk disclosure
INSERT OR IGNORE INTO risk_disclosures (user_id, disclosure_type, disclosure_version)
VALUES (1, 'general_risk', '1.0'); 