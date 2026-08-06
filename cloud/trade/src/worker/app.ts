import { Hono } from "hono";
import type { Context } from "hono";
import type { AuthUser, Env, TradeProfile } from "./types";
import { AuthService, requirePermission } from "./lib/auth";
import { createBroker } from "./lib/broker";
import { newId } from "./lib/crypto";
import { fetchMovers } from "./lib/scanner";

type Variables = { user: AuthUser };
type AppEnv = { Bindings: Env; Variables: Variables };

export function createApp() {
  const app = new Hono<AppEnv>();

  app.get("/api/health", (c) =>
    c.json({ ok: true, app: "trade-advisor", env: "local-mvp" }),
  );

  app.post("/api/auth/login", async (c) => {
    const body = await c.req.json<{ email?: string; password?: string }>();
    if (!body.email || !body.password) {
      return c.json({ error: "email and password required" }, 400);
    }
    const auth = new AuthService(c.env);
    const result = await auth.login(body.email, body.password);
    if (!result.ok) {
      return c.json({ error: result.error }, result.status);
    }
    const host = new URL(c.req.url).hostname;
    const secure = host !== "localhost" && host !== "127.0.0.1";
    const cookie = [
      `trade_session=${result.token}`,
      "Path=/",
      "HttpOnly",
      "SameSite=Lax",
      `Max-Age=${result.maxAge}`,
      ...(secure ? ["Secure"] : []),
    ].join("; ");
    c.header("Set-Cookie", cookie);
    return c.json({ user: result.user });
  });

  app.post("/api/auth/logout", async (c) => {
    const auth = new AuthService(c.env);
    const token = auth.readCookie(c.req.header("Cookie") ?? null);
    await auth.logout(token);
    c.header(
      "Set-Cookie",
      "trade_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0",
    );
    return c.json({ ok: true });
  });

  app.get("/api/auth/me", async (c) => {
    const user = await resolveUser(c);
    if (!user) return c.json({ error: "Unauthorized" }, 401);
    return c.json({ user });
  });

  app.use("/api/*", async (c, next) => {
    if (c.req.path.startsWith("/api/auth/") || c.req.path === "/api/health") {
      return next();
    }
    const user = await resolveUser(c);
    if (!user) return c.json({ error: "Unauthorized" }, 401);
    c.set("user", user);
    return next();
  });

  app.get("/api/profile", async (c) => {
    const user = c.get("user");
    const row = await c.env.DB.prepare(
      `SELECT user_id, risk_tolerance, investment_goals, max_position_pct,
              stop_loss_pct, take_profit_pct, portfolio_value
       FROM trade_profiles WHERE user_id = ?`,
    )
      .bind(user.id)
      .first<TradeProfile>();
    if (!row) {
      return c.json({
        profile: {
          user_id: user.id,
          risk_tolerance: "moderate" as const,
          investment_goals: null,
          max_position_pct: 0.1,
          stop_loss_pct: 0.05,
          take_profit_pct: 0.15,
          portfolio_value: 100000,
        },
      });
    }
    return c.json({ profile: row });
  });

  app.put("/api/profile", async (c) => {
    const user = c.get("user");
    const body = await c.req.json<Partial<TradeProfile>>();
    const risk = body.risk_tolerance ?? "moderate";
    if (!["conservative", "moderate", "aggressive"].includes(risk)) {
      return c.json({ error: "invalid risk_tolerance" }, 400);
    }
    await c.env.DB.prepare(
      `INSERT INTO trade_profiles (
         user_id, risk_tolerance, investment_goals, max_position_pct,
         stop_loss_pct, take_profit_pct, portfolio_value, created_at, updated_at
       ) VALUES (?, ?, ?, ?, ?, ?, ?, unixepoch(), unixepoch())
       ON CONFLICT(user_id) DO UPDATE SET
         risk_tolerance = excluded.risk_tolerance,
         investment_goals = excluded.investment_goals,
         max_position_pct = excluded.max_position_pct,
         stop_loss_pct = excluded.stop_loss_pct,
         take_profit_pct = excluded.take_profit_pct,
         portfolio_value = excluded.portfolio_value,
         updated_at = unixepoch()`,
    )
      .bind(
        user.id,
        risk,
        body.investment_goals ?? null,
        body.max_position_pct ?? 0.1,
        body.stop_loss_pct ?? 0.05,
        body.take_profit_pct ?? 0.15,
        body.portfolio_value ?? 100000,
      )
      .run();
    return c.json({ ok: true });
  });

  app.get("/api/watchlists", async (c) => {
    const user = c.get("user");
    const lists = await c.env.DB.prepare(
      `SELECT id, user_id, name, description, is_default
       FROM trade_watchlists WHERE user_id = ? ORDER BY is_default DESC, name`,
    )
      .bind(user.id)
      .all<{
        id: string;
        user_id: string;
        name: string;
        description: string | null;
        is_default: number;
      }>();

    const result = [];
    for (const list of lists.results || []) {
      const symbols = await c.env.DB.prepare(
        `SELECT id, watchlist_id, symbol, notes FROM trade_watchlist_symbols
         WHERE watchlist_id = ? ORDER BY symbol`,
      )
        .bind(list.id)
        .all();
      result.push({ ...list, symbols: symbols.results || [] });
    }
    return c.json({ watchlists: result });
  });

  app.post("/api/watchlists", async (c) => {
    const user = c.get("user");
    const body = await c.req.json<{ name?: string; description?: string }>();
    if (!body.name?.trim()) return c.json({ error: "name required" }, 400);
    const id = newId("wl");
    await c.env.DB.prepare(
      `INSERT INTO trade_watchlists (id, user_id, name, description, is_default, created_at, updated_at)
       VALUES (?, ?, ?, ?, 0, unixepoch(), unixepoch())`,
    )
      .bind(id, user.id, body.name.trim(), body.description ?? null)
      .run();
    return c.json({ id }, 201);
  });

  app.post("/api/watchlists/:id/symbols", async (c) => {
    const user = c.get("user");
    const watchlistId = c.req.param("id");
    const body = await c.req.json<{ symbol?: string; notes?: string }>();
    if (!body.symbol?.trim()) return c.json({ error: "symbol required" }, 400);
    const owned = await c.env.DB.prepare(
      `SELECT id FROM trade_watchlists WHERE id = ? AND user_id = ?`,
    )
      .bind(watchlistId, user.id)
      .first();
    if (!owned) return c.json({ error: "watchlist not found" }, 404);
    const id = newId("wls");
    try {
      await c.env.DB.prepare(
        `INSERT INTO trade_watchlist_symbols (id, watchlist_id, symbol, notes, added_at)
         VALUES (?, ?, ?, ?, unixepoch())`,
      )
        .bind(
          id,
          watchlistId,
          body.symbol.trim().toUpperCase(),
          body.notes ?? null,
        )
        .run();
    } catch {
      return c.json({ error: "symbol already on watchlist" }, 409);
    }
    return c.json({ id }, 201);
  });

  app.delete("/api/watchlists/:id/symbols/:symbol", async (c) => {
    const user = c.get("user");
    const watchlistId = c.req.param("id");
    const symbol = c.req.param("symbol").toUpperCase();
    const owned = await c.env.DB.prepare(
      `SELECT id FROM trade_watchlists WHERE id = ? AND user_id = ?`,
    )
      .bind(watchlistId, user.id)
      .first();
    if (!owned) return c.json({ error: "watchlist not found" }, 404);
    await c.env.DB.prepare(
      `DELETE FROM trade_watchlist_symbols WHERE watchlist_id = ? AND symbol = ?`,
    )
      .bind(watchlistId, symbol)
      .run();
    return c.json({ ok: true });
  });

  app.delete("/api/watchlists/:id", async (c) => {
    const user = c.get("user");
    const id = c.req.param("id");
    const result = await c.env.DB.prepare(
      `DELETE FROM trade_watchlists WHERE id = ? AND user_id = ?`,
    )
      .bind(id, user.id)
      .run();
    if (!result.meta.changes) return c.json({ error: "not found" }, 404);
    return c.json({ ok: true });
  });

  app.post("/api/scanner/movers", async (c) => {
    const data = await fetchMovers(c.env);
    return c.json(data);
  });

  app.post("/api/broker/connect", async (c) => {
    const broker = createBroker(c.env);
    try {
      const account = await broker.connect();
      return c.json({ account });
    } catch (e) {
      return c.json(
        { error: e instanceof Error ? e.message : "connect failed" },
        502,
      );
    }
  });

  app.get("/api/broker/account", async (c) => {
    const broker = createBroker(c.env);
    try {
      const account = await broker.getAccount();
      return c.json({ account });
    } catch (e) {
      return c.json(
        { error: e instanceof Error ? e.message : "account failed" },
        502,
      );
    }
  });

  app.get("/api/orders", async (c) => {
    const user = c.get("user");
    const rows = await c.env.DB.prepare(
      `SELECT id, user_id, symbol, side, order_type, quantity, limit_price, status,
              broker, broker_order_id, filled_price, filled_at, created_at
       FROM trade_orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 100`,
    )
      .bind(user.id)
      .all();
    return c.json({ orders: rows.results || [] });
  });

  app.post("/api/orders", async (c) => {
    const user = c.get("user");
    if (!requirePermission(user, "paper_trade")) {
      return c.json({ error: "Missing permission: paper_trade" }, 403);
    }
    const body = await c.req.json<{
      symbol?: string;
      side?: "buy" | "sell";
      order_type?: "market" | "limit";
      quantity?: number;
      limit_price?: number;
    }>();
    if (!body.symbol || !body.side || !body.quantity || body.quantity <= 0) {
      return c.json(
        { error: "symbol, side, and positive quantity required" },
        400,
      );
    }
    if (!["buy", "sell"].includes(body.side)) {
      return c.json({ error: "side must be buy or sell" }, 400);
    }
    const orderType = body.order_type || "market";
    if (
      orderType === "limit" &&
      (body.limit_price == null || body.limit_price <= 0)
    ) {
      return c.json({ error: "limit_price required for limit orders" }, 400);
    }

    const broker = createBroker(c.env);
    const result = await broker.placeOrder({
      symbol: body.symbol,
      side: body.side,
      order_type: orderType,
      quantity: body.quantity,
      limit_price: body.limit_price ?? null,
    });

    const orderId = newId("ord");
    const status =
      result.status === "filled"
        ? "filled"
        : result.status === "rejected"
          ? "rejected"
          : "submitted";
    const filledAt = status === "filled" ? Math.floor(Date.now() / 1000) : null;

    await c.env.DB.prepare(
      `INSERT INTO trade_orders (
         id, user_id, symbol, side, order_type, quantity, limit_price, status,
         broker, broker_order_id, filled_price, filled_at, created_at, updated_at
       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, unixepoch(), unixepoch())`,
    )
      .bind(
        orderId,
        user.id,
        body.symbol.toUpperCase(),
        body.side,
        orderType,
        body.quantity,
        body.limit_price ?? null,
        status,
        result.broker,
        result.broker_order_id,
        result.filled_price,
        filledAt,
      )
      .run();

    if (status === "filled" && result.filled_price != null) {
      await upsertPosition(
        c.env.DB,
        user.id,
        body.symbol.toUpperCase(),
        body.side,
        body.quantity,
        result.filled_price,
      );
    }

    return c.json(
      {
        order: {
          id: orderId,
          status,
          broker: result.broker,
          broker_order_id: result.broker_order_id,
          filled_price: result.filled_price,
          message: result.message,
        },
      },
      status === "rejected" ? 400 : 201,
    );
  });

  app.get("/api/positions", async (c) => {
    const user = c.get("user");
    const broker = createBroker(c.env);

    const dbRows = await c.env.DB.prepare(
      `SELECT id, user_id, symbol, quantity, avg_entry_price, current_price
       FROM trade_positions WHERE user_id = ? ORDER BY symbol`,
    )
      .bind(user.id)
      .all();

    if (broker.name === "alpaca") {
      try {
        const live = await broker.getPositions();
        return c.json({ positions: live, source: "alpaca" });
      } catch {
        /* fall through */
      }
    }

    return c.json({ positions: dbRows.results || [], source: "db" });
  });

  app.notFound(async (c) => {
    if (c.req.path.startsWith("/api/")) {
      return c.json({ error: "Not found" }, 404);
    }
    return c.env.ASSETS.fetch(c.req.raw);
  });

  return app;
}

async function resolveUser(c: Context<AppEnv>): Promise<AuthUser | null> {
  const auth = new AuthService(c.env);
  const token = auth.readCookie(c.req.header("Cookie") ?? null);
  return auth.resolveSession(token);
}

async function upsertPosition(
  db: D1Database,
  userId: string,
  symbol: string,
  side: "buy" | "sell",
  quantity: number,
  price: number,
): Promise<void> {
  const existing = await db
    .prepare(
      `SELECT id, quantity, avg_entry_price FROM trade_positions
       WHERE user_id = ? AND symbol = ?`,
    )
    .bind(userId, symbol)
    .first<{ id: string; quantity: number; avg_entry_price: number }>();

  if (side === "buy") {
    if (!existing) {
      await db
        .prepare(
          `INSERT INTO trade_positions
             (id, user_id, symbol, quantity, avg_entry_price, current_price, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, unixepoch())`,
        )
        .bind(newId("pos"), userId, symbol, quantity, price, price)
        .run();
      return;
    }
    const qty = existing.quantity + quantity;
    const avg =
      (existing.avg_entry_price * existing.quantity + price * quantity) / qty;
    await db
      .prepare(
        `UPDATE trade_positions
         SET quantity = ?, avg_entry_price = ?, current_price = ?, updated_at = unixepoch()
         WHERE id = ?`,
      )
      .bind(qty, avg, price, existing.id)
      .run();
    return;
  }

  if (!existing) return;
  const remaining = existing.quantity - quantity;
  if (remaining <= 0) {
    await db
      .prepare(`DELETE FROM trade_positions WHERE id = ?`)
      .bind(existing.id)
      .run();
  } else {
    await db
      .prepare(
        `UPDATE trade_positions
         SET quantity = ?, current_price = ?, updated_at = unixepoch()
         WHERE id = ?`,
      )
      .bind(remaining, price, existing.id)
      .run();
  }
}

export default createApp();
