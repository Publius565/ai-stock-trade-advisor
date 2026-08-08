export type AuthUser = {
  id: string;
  email: string;
  name: string | null;
  role: string;
  permissions: Record<string, boolean | undefined>;
};

async function parseJson<T>(res: Response): Promise<T> {
  const data = (await res.json()) as T & { error?: string };
  if (!res.ok) {
    throw new Error((data as { error?: string }).error || res.statusText);
  }
  return data;
}

export const api = {
  async login(email: string, password: string) {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email, password }),
    });
    return parseJson<{ user: AuthUser }>(res);
  },
  async logout() {
    const res = await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });
    return parseJson<{ ok: boolean }>(res);
  },
  async me() {
    const res = await fetch("/api/auth/me", { credentials: "include" });
    return parseJson<{ user: AuthUser }>(res);
  },
  async getProfile() {
    const res = await fetch("/api/profile", { credentials: "include" });
    return parseJson<{ profile: Record<string, unknown> }>(res);
  },
  async putProfile(profile: Record<string, unknown>) {
    const res = await fetch("/api/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(profile),
    });
    return parseJson<{ ok: boolean }>(res);
  },
  async getWatchlists() {
    const res = await fetch("/api/watchlists", { credentials: "include" });
    return parseJson<{ watchlists: Array<Record<string, unknown>> }>(res);
  },
  async addSymbol(watchlistId: string, symbol: string) {
    const res = await fetch(`/api/watchlists/${watchlistId}/symbols`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ symbol }),
    });
    return parseJson<{ id: string }>(res);
  },
  async removeSymbol(watchlistId: string, symbol: string) {
    const res = await fetch(
      `/api/watchlists/${watchlistId}/symbols/${encodeURIComponent(symbol)}`,
      { method: "DELETE", credentials: "include" },
    );
    return parseJson<{ ok: boolean }>(res);
  },
  async scanMovers() {
    const res = await fetch("/api/scanner/movers", {
      method: "POST",
      credentials: "include",
    });
    return parseJson<{
      source: string;
      movers: Array<{
        symbol: string;
        change_pct: number;
        price: number;
        volume: number;
      }>;
    }>(res);
  },
  async connectBroker() {
    const res = await fetch("/api/broker/connect", {
      method: "POST",
      credentials: "include",
    });
    return parseJson<{ account: Record<string, unknown> }>(res);
  },
  async getAccount() {
    const res = await fetch("/api/broker/account", { credentials: "include" });
    return parseJson<{ account: Record<string, unknown> }>(res);
  },
  async getOrders() {
    const res = await fetch("/api/orders", { credentials: "include" });
    return parseJson<{ orders: Array<Record<string, unknown>> }>(res);
  },
  async placeOrder(body: {
    symbol: string;
    side: "buy" | "sell";
    quantity: number;
    order_type?: "market" | "limit";
    limit_price?: number;
  }) {
    const res = await fetch("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body),
    });
    return parseJson<{ order: Record<string, unknown> }>(res);
  },
  async getPositions() {
    const res = await fetch("/api/positions", { credentials: "include" });
    return parseJson<{
      positions: Array<Record<string, unknown>>;
      source: string;
    }>(res);
  },
};
