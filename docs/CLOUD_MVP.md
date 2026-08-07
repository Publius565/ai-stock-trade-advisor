# Cloudflare Trade MVP — Runbook

Cloud agent–executable MVP for Agent Green on Cloudflare (local Wrangler). Desktop Python app is unchanged.

## Quick start
See [`cloud/trade/README.md`](../cloud/trade/README.md).

```bash
cd cloud/trade && npm install && cp .dev.vars.example .dev.vars
npm run build:web && npm run db:setup:local && npm run preview
```

Open http://127.0.0.1:8787 — login `trader@example.com` / `password123`.

## Production
- **AGE-8 done:** bound to `publiusly-db`, auth adapter + Publiusly PBKDF2 hash, additive remote tables (`sessions`, `app_memberships`, `trade_*`)
- **AGE-9:** secrets + deploy + DNS `trade.publius.com`
- **AGE-10:** grant `app_memberships` for real users (`app_id='trade'`)

## API
- Auth: `POST /api/auth/login|logout`, `GET /api/auth/me`
- Profile, watchlists, scanner movers
- Broker connect/account, orders, positions (MockBroker without Alpaca secrets)
