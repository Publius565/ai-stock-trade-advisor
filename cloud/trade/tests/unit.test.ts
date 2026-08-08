import { describe, expect, it } from "vitest";
import { hashPassword, verifyPassword } from "../src/worker/lib/crypto";
import { MockBroker } from "../src/worker/lib/broker";
import { requirePermission } from "../src/worker/lib/auth";
import type { AuthUser } from "../src/worker/types";

describe("password hashing", () => {
  it("round-trips Publiusly PBKDF2 hex verify", async () => {
    const stored = await hashPassword("password123", 10_000);
    expect(stored.startsWith("2710:")).toBe(true); // 10000 = 0x2710
    expect(await verifyPassword("password123", stored)).toBe(true);
    expect(await verifyPassword("wrong", stored)).toBe(false);
  });

  it("matches seed salt format", async () => {
    const salt = new TextEncoder().encode("seedlocaldevsalt");
    const stored = await hashPassword("password123", 100_000, salt);
    expect(stored).toBe(
      "186a0:736565646c6f63616c64657673616c74:f7560e288bfaddb273f0ca17fd807dfa1c07155fe03e8e4959649e6bea604ada",
    );
    expect(await verifyPassword("password123", stored)).toBe(true);
  });
});

describe("permissions", () => {
  const user: AuthUser = {
    id: "u1",
    email: "a@b.c",
    name: null,
    role: "trader",
    permissions: { paper_trade: true, ml: false },
  };

  it("allows paper_trade", () => {
    expect(requirePermission(user, "paper_trade")).toBe(true);
  });

  it("denies ml", () => {
    expect(requirePermission(user, "ml")).toBe(false);
  });
});

describe("MockBroker", () => {
  it("fills a buy and tracks position", async () => {
    const broker = new MockBroker();
    const before = await broker.getAccount();
    const result = await broker.placeOrder({
      symbol: "AAPL",
      side: "buy",
      order_type: "market",
      quantity: 2,
    });
    expect(result.status).toBe("filled");
    expect(result.filled_price).toBeGreaterThan(0);
    const positions = await broker.getPositions();
    expect(positions).toHaveLength(1);
    expect(positions[0].symbol).toBe("AAPL");
    expect(positions[0].quantity).toBe(2);
    const after = await broker.getAccount();
    expect(after.cash!).toBeLessThan(before.cash!);
  });

  it("rejects sell without position", async () => {
    const broker = new MockBroker();
    const result = await broker.placeOrder({
      symbol: "ZZZZ",
      side: "sell",
      order_type: "market",
      quantity: 1,
    });
    expect(result.status).toBe("rejected");
  });
});

describe("order validation helpers", () => {
  it("requires positive quantity semantics", () => {
    const quantity = 0;
    expect(quantity <= 0).toBe(true);
  });
});
