# Cloudflare Trade MVP — Runbook

Cloud agent–executable MVP for Agent Green on Cloudflare (local Wrangler). Desktop Python app is unchanged.

## Quick start
See [`cloud/trade/README.md`](../cloud/trade/README.md).

```bash
cd cloud/trade && npm install && cp .dev.vars.example .dev.vars
npm run build:web && npm run db:setup:local && npm run preview
```

Open http://127.0.0.1:8787 — login `trader@example.com` / `password123`.

## Home finalize (production)
1. Cloudflare auth + bind Publiusly D1 `database_id`
2. Align `users` adapter + password verify to live schema
3. Secrets + deploy + DNS `trade.publius.com`
4. Grant `app_memberships` for real users (`app_id='trade'`)

## API
- Auth: `POST /api/auth/login|logout`, `GET /api/auth/me`
- Profile, watchlists, scanner movers
- Broker connect/account, orders, positions (MockBroker without Alpaca secrets)
