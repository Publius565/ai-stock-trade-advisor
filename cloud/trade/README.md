# Trade Advisor Cloudflare MVP

Offline-executable Cloudflare Pages + Worker + D1 app for Agent Green paper trading.

## Local run (no Cloudflare account)

```bash
cd cloud/trade
npm install
cp .dev.vars.example .dev.vars
npm run build:web
npm run db:setup:local
npm run preview   # wrangler dev on :8787 with SPA + API
```

Optional split: `npm run dev:worker` (API+assets) and `npm run dev` (Vite on :5173 proxying `/api` → :8787).

### Seed users
| Email | Password | Trade access |
|-------|----------|--------------|
| `trader@example.com` | `password123` | Yes (`paper_trade`) |
| `noaccess@example.com` | `password123` | No → login **403 AppAccessDenied** |

### Verify
```bash
npm test
curl -s http://127.0.0.1:8787/api/health
# Login then call authenticated routes with cookie jar
```

## Layout
- `src/worker/` — Hono API, auth, MockBroker/Alpaca, scanner
- `src/web/` — React SPA
- `migrations/` — D1 schema (Publiusly `users`/`user_credentials` mirror + `app_memberships` + `trade_*`)
- `scripts/seed-local.sql` — local demo data only (never seed remote)

## Identity model
Shared production D1 **`publiusly-db`** (bound in `wrangler.jsonc`):
- `users` + `user_credentials` — Publiusly identity (do not recreate on prod)
- `app_memberships` — `app_id = 'trade'`, `permissions_json` e.g. `{"paper_trade":true}`
- `sessions` — trade-owned HttpOnly `trade_session` cookie (separate from Publiusly JWT/`refresh_tokens`)

Password format (Publiusly): `iterationsHex:saltHex:hashHex` (Web Crypto PBKDF2-SHA256, 100000 iters). Login requires `email_verified = 1`.

## Production status (AGE-8 done)
1. ~~Bind Publiusly D1 `database_id`~~ — done
2. ~~Align `UserRepository` / `verifyPassword`~~ — done
3. ~~Apply additive migrations remotely~~ (`sessions`, `app_memberships`, `trade_*`) — done
4. Secrets + deploy + DNS `trade.publius.com` — **AGE-9**
5. `INSERT` `app_memberships` for real Publiusly users — **AGE-10**

```bash
# Additive remote schema (already applied once):
npm run db:migrate:remote
```

## Out of MVP
ML predictions UI, signals polish, portfolio analytics/backtesting, continuous scanners, sklearn training (Containers later).
