import type { BrokerAccount, Env, OrderSide, OrderType } from "../types";
import { newId } from "./crypto";

export type PlaceOrderInput = {
  symbol: string;
  side: OrderSide;
  order_type: OrderType;
  quantity: number;
  limit_price?: number | null;
};

export type PlaceOrderResult = {
  broker: string;
  broker_order_id: string;
  status: "submitted" | "filled" | "rejected";
  filled_price: number | null;
  message?: string;
};

export interface Broker {
  name: string;
  connect(): Promise<BrokerAccount>;
  getAccount(): Promise<BrokerAccount>;
  placeOrder(input: PlaceOrderInput): Promise<PlaceOrderResult>;
  getPositions(): Promise<
    Array<{
      symbol: string;
      quantity: number;
      avg_entry_price: number;
      current_price: number | null;
    }>
  >;
}

/** In-memory paper broker for local runs without Alpaca secrets. */
export class MockBroker implements Broker {
  name = "mock";
  private cash = 100_000;
  private positions = new Map<
    string,
    { quantity: number; avg_entry_price: number; current_price: number }
  >();

  async connect(): Promise<BrokerAccount> {
    return this.getAccount();
  }

  async getAccount(): Promise<BrokerAccount> {
    let equity = this.cash;
    for (const p of this.positions.values()) {
      equity += p.quantity * p.current_price;
    }
    return {
      broker: this.name,
      connected: true,
      account_id: "mock-paper-001",
      status: "ACTIVE",
      buying_power: this.cash,
      cash: this.cash,
      portfolio_value: equity,
      equity,
    };
  }

  async placeOrder(input: PlaceOrderInput): Promise<PlaceOrderResult> {
    const symbol = input.symbol.toUpperCase();
    const price = mockPrice(symbol);
    const notional = price * input.quantity;

    if (input.side === "buy") {
      if (notional > this.cash) {
        return {
          broker: this.name,
          broker_order_id: newId("ord"),
          status: "rejected",
          filled_price: null,
          message: "Insufficient buying power",
        };
      }
      this.cash -= notional;
      const existing = this.positions.get(symbol);
      if (existing) {
        const qty = existing.quantity + input.quantity;
        const avg =
          (existing.avg_entry_price * existing.quantity + notional) / qty;
        this.positions.set(symbol, {
          quantity: qty,
          avg_entry_price: avg,
          current_price: price,
        });
      } else {
        this.positions.set(symbol, {
          quantity: input.quantity,
          avg_entry_price: price,
          current_price: price,
        });
      }
    } else {
      const existing = this.positions.get(symbol);
      if (!existing || existing.quantity < input.quantity) {
        return {
          broker: this.name,
          broker_order_id: newId("ord"),
          status: "rejected",
          filled_price: null,
          message: "Insufficient position",
        };
      }
      this.cash += notional;
      const remaining = existing.quantity - input.quantity;
      if (remaining <= 0) this.positions.delete(symbol);
      else
        this.positions.set(symbol, {
          ...existing,
          quantity: remaining,
          current_price: price,
        });
    }

    return {
      broker: this.name,
      broker_order_id: newId("alpaca_mock"),
      status: "filled",
      filled_price: price,
    };
  }

  async getPositions() {
    return [...this.positions.entries()].map(([symbol, p]) => ({
      symbol,
      quantity: p.quantity,
      avg_entry_price: p.avg_entry_price,
      current_price: p.current_price,
    }));
  }
}

export class AlpacaBroker implements Broker {
  name = "alpaca";
  private baseUrl: string;

  constructor(
    private apiKey: string,
    private secretKey: string,
    baseUrl?: string,
  ) {
    this.baseUrl = (baseUrl || "https://paper-api.alpaca.markets").replace(
      /\/$/,
      "",
    );
  }

  private headers(): HeadersInit {
    return {
      "APCA-API-KEY-ID": this.apiKey,
      "APCA-API-SECRET-KEY": this.secretKey,
      "Content-Type": "application/json",
    };
  }

  async connect(): Promise<BrokerAccount> {
    return this.getAccount();
  }

  async getAccount(): Promise<BrokerAccount> {
    const res = await fetch(`${this.baseUrl}/v2/account`, {
      headers: this.headers(),
    });
    if (!res.ok) {
      throw new Error(`Alpaca account error: ${res.status}`);
    }
    const account = (await res.json()) as Record<string, string>;
    return {
      broker: this.name,
      connected: true,
      account_id: account.id,
      status: account.status,
      buying_power: Number(account.buying_power),
      cash: Number(account.cash),
      portfolio_value: Number(account.portfolio_value),
      equity: Number(account.equity),
    };
  }

  async placeOrder(input: PlaceOrderInput): Promise<PlaceOrderResult> {
    const body: Record<string, unknown> = {
      symbol: input.symbol.toUpperCase(),
      qty: String(input.quantity),
      side: input.side,
      type: input.order_type,
      time_in_force: "day",
    };
    if (input.order_type === "limit" && input.limit_price != null) {
      body.limit_price = String(input.limit_price);
    }
    const res = await fetch(`${this.baseUrl}/v2/orders`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify(body),
    });
    const data = (await res.json()) as Record<string, string>;
    if (!res.ok) {
      return {
        broker: this.name,
        broker_order_id: data.id || newId("rej"),
        status: "rejected",
        filled_price: null,
        message: data.message || `Alpaca error ${res.status}`,
      };
    }
    const filled =
      data.filled_avg_price != null ? Number(data.filled_avg_price) : null;
    const status =
      data.status === "filled"
        ? "filled"
        : data.status === "rejected"
          ? "rejected"
          : "submitted";
    return {
      broker: this.name,
      broker_order_id: data.id,
      status,
      filled_price: filled,
    };
  }

  async getPositions() {
    const res = await fetch(`${this.baseUrl}/v2/positions`, {
      headers: this.headers(),
    });
    if (!res.ok) throw new Error(`Alpaca positions error: ${res.status}`);
    const rows = (await res.json()) as Array<Record<string, string>>;
    return rows.map((p) => ({
      symbol: p.symbol,
      quantity: Number(p.qty),
      avg_entry_price: Number(p.avg_entry_price),
      current_price: Number(p.current_price),
    }));
  }
}

export function createBroker(env: Env): Broker {
  if (env.ALPACA_API_KEY && env.ALPACA_SECRET_KEY) {
    return new AlpacaBroker(
      env.ALPACA_API_KEY,
      env.ALPACA_SECRET_KEY,
      env.ALPACA_BASE_URL,
    );
  }
  return new MockBroker();
}

function mockPrice(symbol: string): number {
  let hash = 0;
  for (let i = 0; i < symbol.length; i++) {
    hash = (hash * 31 + symbol.charCodeAt(i)) >>> 0;
  }
  return 50 + (hash % 400) + (hash % 100) / 100;
}
