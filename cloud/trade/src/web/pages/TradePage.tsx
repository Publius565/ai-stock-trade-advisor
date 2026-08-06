import { FormEvent, useEffect, useState } from "react";
import { api } from "../api";

export function TradePage() {
  const [account, setAccount] = useState<Record<string, unknown> | null>(null);
  const [orders, setOrders] = useState<Array<Record<string, unknown>>>([]);
  const [symbol, setSymbol] = useState("AAPL");
  const [side, setSide] = useState<"buy" | "sell">("buy");
  const [quantity, setQuantity] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const refresh = async () => {
    const [acct, ord] = await Promise.all([api.connectBroker(), api.getOrders()]);
    setAccount(acct.account);
    setOrders(ord.orders);
  };

  useEffect(() => {
    void refresh().catch((e) => setError(e.message));
  }, []);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    try {
      const { order } = await api.placeOrder({ symbol, side, quantity });
      setMessage(
        `Order ${String(order.status)} @ ${order.filled_price ?? "n/a"} (${String(order.broker)})`,
      );
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Order failed");
    }
  };

  return (
    <div>
      <h2 className="page-title">Paper trade</h2>
      <p className="page-lead">
        Places orders via MockBroker locally, or Alpaca paper when secrets are set.
      </p>
      {account && (
        <div className="panel stat-row">
          <div className="stat">
            <span className="muted">Broker</span>
            <strong>{String(account.broker)}</strong>
          </div>
          <div className="stat">
            <span className="muted">Buying power</span>
            <strong>
              $
              {Number(account.buying_power ?? 0).toLocaleString(undefined, {
                maximumFractionDigits: 0,
              })}
            </strong>
          </div>
          <div className="stat">
            <span className="muted">Equity</span>
            <strong>
              $
              {Number(account.equity ?? 0).toLocaleString(undefined, {
                maximumFractionDigits: 0,
              })}
            </strong>
          </div>
        </div>
      )}
      <form className="panel" onSubmit={(e) => void submit(e)}>
        <div className="grid-2">
          <div>
            <label htmlFor="symbol">Symbol</label>
            <input
              id="symbol"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            />
          </div>
          <div>
            <label htmlFor="side">Side</label>
            <select
              id="side"
              value={side}
              onChange={(e) => setSide(e.target.value as "buy" | "sell")}
            >
              <option value="buy">Buy</option>
              <option value="sell">Sell</option>
            </select>
          </div>
        </div>
        <label htmlFor="qty">Quantity</label>
        <input
          id="qty"
          type="number"
          min={1}
          step={1}
          value={quantity}
          onChange={(e) => setQuantity(Number(e.target.value))}
        />
        {error && <p className="error">{error}</p>}
        {message && <p className="muted">{message}</p>}
        <button type="submit">Submit market order</button>
      </form>
      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Recent orders</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Side</th>
              <th>Qty</th>
              <th>Status</th>
              <th>Fill</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={String(o.id)}>
                <td>{String(o.symbol)}</td>
                <td>{String(o.side)}</td>
                <td>{String(o.quantity)}</td>
                <td>{String(o.status)}</td>
                <td>
                  {o.filled_price != null
                    ? `$${Number(o.filled_price).toFixed(2)}`
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
