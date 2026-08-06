import { useEffect, useState } from "react";
import { api } from "../api";

export function PositionsPage() {
  const [positions, setPositions] = useState<Array<Record<string, unknown>>>([]);
  const [source, setSource] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void api
      .getPositions()
      .then((r) => {
        setPositions(r.positions);
        setSource(r.source);
      })
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div>
      <h2 className="page-title">Positions</h2>
      <p className="page-lead">
        Open positions {source ? `(source: ${source})` : ""}
      </p>
      {error && <p className="error">{error}</p>}
      <div className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Qty</th>
              <th>Avg entry</th>
              <th>Current</th>
            </tr>
          </thead>
          <tbody>
            {positions.length === 0 && (
              <tr>
                <td colSpan={4} className="muted">
                  No open positions
                </td>
              </tr>
            )}
            {positions.map((p, i) => (
              <tr key={String(p.id ?? `${p.symbol}-${i}`)}>
                <td>{String(p.symbol)}</td>
                <td>{String(p.quantity)}</td>
                <td>${Number(p.avg_entry_price).toFixed(2)}</td>
                <td>
                  {p.current_price != null
                    ? `$${Number(p.current_price).toFixed(2)}`
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
