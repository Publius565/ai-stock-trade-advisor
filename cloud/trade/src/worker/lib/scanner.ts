import type { Env, Mover } from "../types";

const MOCK_MOVERS: Mover[] = [
  { symbol: "NVDA", change_pct: 4.2, price: 875.1, volume: 42_000_000 },
  { symbol: "TSLA", change_pct: 3.1, price: 248.5, volume: 88_000_000 },
  { symbol: "AAPL", change_pct: 1.4, price: 198.2, volume: 55_000_000 },
  { symbol: "AMD", change_pct: -2.3, price: 162.4, volume: 61_000_000 },
  { symbol: "META", change_pct: -1.1, price: 512.8, volume: 18_000_000 },
];

/**
 * Market movers: Alpha Vantage if key present, else stable mock data for local MVP.
 */
export async function fetchMovers(env: Env): Promise<{
  source: "alpha_vantage" | "mock";
  movers: Mover[];
}> {
  const key = env.ALPHA_VANTAGE_API_KEY;
  if (!key) {
    return { source: "mock", movers: MOCK_MOVERS };
  }

  try {
    const url = `https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey=${encodeURIComponent(key)}`;
    const res = await fetch(url);
    if (!res.ok) return { source: "mock", movers: MOCK_MOVERS };
    const data = (await res.json()) as {
      top_gainers?: Array<Record<string, string>>;
      top_losers?: Array<Record<string, string>>;
    };
    const gainers = (data.top_gainers || []).slice(0, 5).map(mapAv);
    const losers = (data.top_losers || []).slice(0, 5).map(mapAv);
    const movers = [...gainers, ...losers].filter((m) => m.symbol);
    if (!movers.length) return { source: "mock", movers: MOCK_MOVERS };
    return { source: "alpha_vantage", movers };
  } catch {
    return { source: "mock", movers: MOCK_MOVERS };
  }
}

function mapAv(row: Record<string, string>): Mover {
  return {
    symbol: row.ticker || row.symbol || "",
    change_pct: Number(row.change_percentage?.replace("%", "") || 0),
    price: Number(row.price || 0),
    volume: Number(row.volume || 0),
  };
}
