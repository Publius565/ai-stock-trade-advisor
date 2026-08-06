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
- `migrations/` — D1 schema (`users` mirror, `app_memberships`, `trade_*`)
- `scripts/seed-local.sql` — local demo data

## Identity model
Shared Publiusly-style D1:
- `users` — local mirror (align columns/hash to production at home via `UserRepository` in `src/worker/lib/auth.ts`)
- `app_memberships` — `app_id = 'trade'`, `permissions_json` e.g. `{"paper_trade":true}`
- Sessions: HttpOnly `trade_session` cookie

Password format (local MVP): `pbkdf2$iterations$saltB64$hashB64` (Web Crypto PBKDF2-SHA256).

## Home finalize checklist
1. `wrangler login` (or set `CLOUDFLARE_API_TOKEN` + account id)
2. Set `database_id` in [`wrangler.jsonc`](../cloud/trade/wrangler.jsonc) to the **Publiusly production D1** id (same binding both Workers can use)
3. Apply only **new** migrations (`app_memberships`, `trade_*`, `sessions` if missing) — do **not** recreate production `users`
4. Align `UserRepository` / `verifyPassword` to live Publiusly column names and hash algorithm
5. `wrangler secret put SESSION_SECRET` (and optional `ALPACA_*`, `ALPHA_VANTAGE_API_KEY`)
6. Deploy Worker/Pages; attach custom domain **`trade.publius.com`** (CNAME on `publius.com` zone — leave apex alone)
7. `INSERT` `app_memberships` rows for real Publiusly users who should access Trade

## Out of MVP
ML predictions UI, signals polish, portfolio analytics/backtesting, continuous scanners, sklearn training (Containers later).
