import { useAuth } from "../auth";

export function DashboardPage() {
  const { user } = useAuth();
  return (
    <div>
      <h2 className="page-title">Welcome</h2>
      <p className="page-lead">
        Paper trading workspace for {user?.name || user?.email}. Membership role:{" "}
        <strong>{user?.role}</strong>
      </p>
      <div className="panel">
        <div className="stat-row">
          <div className="stat">
            <span className="muted">Paper trade</span>
            <strong>{user?.permissions.paper_trade ? "Enabled" : "Off"}</strong>
          </div>
          <div className="stat">
            <span className="muted">ML (later)</span>
            <strong>{user?.permissions.ml ? "Enabled" : "Off"}</strong>
          </div>
        </div>
        <p className="muted" style={{ marginTop: "1rem", marginBottom: 0 }}>
          Use the sidebar for profile, watchlist, scanner, orders, and positions.
        </p>
      </div>
    </div>
  );
}
