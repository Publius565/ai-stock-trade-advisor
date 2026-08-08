import { FormEvent, useEffect, useState } from "react";
import { api } from "../api";

type SymbolRow = { id: string; symbol: string; notes: string | null };
type Watchlist = {
  id: string;
  name: string;
  description: string | null;
  symbols: SymbolRow[];
};

export function WatchlistPage() {
  const [lists, setLists] = useState<Watchlist[]>([]);
  const [symbol, setSymbol] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    const { watchlists } = await api.getWatchlists();
    setLists(watchlists as Watchlist[]);
  };

  useEffect(() => {
    void load().catch((e) => setError(e.message));
  }, []);

  const primary = lists[0];

  const add = async (e: FormEvent) => {
    e.preventDefault();
    if (!primary || !symbol.trim()) return;
    setError(null);
    try {
      await api.addSymbol(primary.id, symbol.trim());
      setSymbol("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Add failed");
    }
  };

  const remove = async (sym: string) => {
    if (!primary) return;
    await api.removeSymbol(primary.id, sym);
    await load();
  };

  return (
    <div>
      <h2 className="page-title">Watchlist</h2>
      <p className="page-lead">
        {primary ? primary.name : "No watchlist yet"} — track symbols for scanning.
      </p>
      {primary && (
        <form className="panel" onSubmit={(e) => void add(e)}>
          <label htmlFor="sym">Add symbol</label>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <input
              id="sym"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="AAPL"
            />
            <button type="submit">Add</button>
          </div>
          {error && <p className="error">{error}</p>}
        </form>
      )}
      <div className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Notes</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {(primary?.symbols || []).map((s) => (
              <tr key={s.id}>
                <td>{s.symbol}</td>
                <td className="muted">{s.notes || "—"}</td>
                <td>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => void remove(s.symbol)}
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
