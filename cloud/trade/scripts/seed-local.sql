-- Local seed for wrangler D1.
-- Password for trader@example.com is: password123
-- Hash = PBKDF2-SHA256 (see scripts/generate-seed-hash.mjs)

INSERT OR IGNORE INTO users (id, email, password_hash, name, created_at, updated_at, is_active)
VALUES (
  'user_trader_001',
  'trader@example.com',
  'pbkdf2$100000$c2VlZGxvY2FsZGV2c2FsdA==$91YOKIv63bJz8MoX/YB9+hwHFV/gPo5JWWSea+pgSto=',
  'Demo Trader',
  unixepoch(),
  unixepoch(),
  1
);

-- User without trade access (login should 403 AppAccessDenied)
INSERT OR IGNORE INTO users (id, email, password_hash, name, created_at, updated_at, is_active)
VALUES (
  'user_noaccess_001',
  'noaccess@example.com',
  'pbkdf2$100000$c2VlZGxvY2FsZGV2c2FsdA==$91YOKIv63bJz8MoX/YB9+hwHFV/gPo5JWWSea+pgSto=',
  'No Access User',
  unixepoch(),
  unixepoch(),
  1
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
