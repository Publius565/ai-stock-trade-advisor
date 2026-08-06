import { useState } from "react";
import { api } from "../api";

type Mover = {
  symbol: string;
  change_pct: number;
  price: number;
  volume: number;
};

export function ScannerPage() {
  const [movers, setMovers] = useState<Mover[]>([]);
  const [source, setSource] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const scan = async () => {
    setBusy(true);
    setError(null);
    try {
      const data = await api.scanMovers();
      setMovers(data.movers);
      setSource(data.source);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <h2 className="page-title">Market scanner</h2>
      <p className="page-lead">Top movers — mock data locally, Alpha Vantage when keyed.</p>
      <button type="button" onClick={() => void scan()} disabled={busy}>
        {busy ? "Scanning…" : "Run scan"}
      </button>
      {source && (
        <p className="muted" style={{ marginTop: "0.75rem" }}>
          Source: {source}
        </p>
      )}
      {error && <p className="error">{error}</p>}
      <div className="panel" style={{ marginTop: "1rem" }}>
        <table className="table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Change %</th>
              <th>Price</th>
              <th>Volume</th>
            </tr>
          </thead>
          <tbody>
            {movers.map((m) => (
              <tr key={m.symbol}>
                <td>{m.symbol}</td>
                <td style={{ color: m.change_pct >= 0 ? "var(--accent)" : "var(--danger)" }}>
                  {m.change_pct.toFixed(2)}%
                </td>
                <td>${m.price.toFixed(2)}</td>
                <td>{m.volume.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
