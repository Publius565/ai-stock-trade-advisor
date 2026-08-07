-- Local seed for wrangler D1 only. NEVER run against remote publiusly-db.
-- Password for both users: password123
-- Hash = Publiusly PBKDF2-SHA256 (see scripts/generate-seed-hash.mjs)

INSERT OR IGNORE INTO users (
  id, email, email_verified, display_name, role, created_at, updated_at, last_login_at
) VALUES (
  'user_trader_001',
  'trader@example.com',
  1,
  'Demo Trader',
  'user',
  '2026-01-01T00:00:00.000Z',
  '2026-01-01T00:00:00.000Z',
  NULL
);

INSERT OR IGNORE INTO users (
  id, email, email_verified, display_name, role, created_at, updated_at, last_login_at
) VALUES (
  'user_noaccess_001',
  'noaccess@example.com',
  1,
  'No Access User',
  'user',
  '2026-01-01T00:00:00.000Z',
  '2026-01-01T00:00:00.000Z',
  NULL
);

INSERT OR IGNORE INTO user_credentials (user_id, password_hash, created_at, updated_at)
VALUES (
  'user_trader_001',
  '186a0:736565646c6f63616c64657673616c74:f7560e288bfaddb273f0ca17fd807dfa1c07155fe03e8e4959649e6bea604ada',
  '2026-01-01T00:00:00.000Z',
  '2026-01-01T00:00:00.000Z'
);

INSERT OR IGNORE INTO user_credentials (user_id, password_hash, created_at, updated_at)
VALUES (
  'user_noaccess_001',
  '186a0:736565646c6f63616c64657673616c74:f7560e288bfaddb273f0ca17fd807dfa1c07155fe03e8e4959649e6bea604ada',
  '2026-01-01T00:00:00.000Z',
  '2026-01-01T00:00:00.000Z'
);

INSERT OR IGNORE INTO app_memberships (
  id, user_id, app_id, role, permissions_json, status, created_at, updated_at
) VALUES (
  'mem_trade_001',
  'user_trader_001',
  'trade',
  'trader',
  '{"paper_trade":true,"ml":false}',
  'active',
  unixepoch(),
  unixepoch()
);

INSERT OR IGNORE INTO trade_profiles (
  user_id, risk_tolerance, investment_goals, max_position_pct,
  stop_loss_pct, take_profit_pct, portfolio_value, created_at, updated_at
) VALUES (
  'user_trader_001',
  'moderate',
  'Grow paper portfolio with disciplined risk',
  0.1,
  0.05,
  0.15,
  100000,
  unixepoch(),
  unixepoch()
);

INSERT OR IGNORE INTO trade_watchlists (id, user_id, name, description, is_default, created_at, updated_at)
VALUES (
  'wl_default_001',
  'user_trader_001',
  'Default',
  'Starter watchlist',
  1,
  unixepoch(),
  unixepoch()
);

INSERT OR IGNORE INTO trade_watchlist_symbols (id, watchlist_id, symbol, notes, added_at)
VALUES
  ('wls_001', 'wl_default_001', 'AAPL', 'Core holding', unixepoch()),
  ('wls_002', 'wl_default_001', 'MSFT', NULL, unixepoch()),
  ('wls_003', 'wl_default_001', 'GOOGL', NULL, unixepoch());
