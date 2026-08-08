import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProfilePage } from "./pages/ProfilePage";
import { WatchlistPage } from "./pages/WatchlistPage";
import { ScannerPage } from "./pages/ScannerPage";
import { TradePage } from "./pages/TradePage";
import { PositionsPage } from "./pages/PositionsPage";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="main muted">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function Shell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1 className="brand">Agent Green</h1>
        <p className="brand-sub">Trade Advisor · paper</p>
        <nav className="nav">
          <NavLink to="/" end>
            Home
          </NavLink>
          <NavLink to="/profile">Profile</NavLink>
          <NavLink to="/watchlist">Watchlist</NavLink>
          <NavLink to="/scanner">Scanner</NavLink>
          <NavLink to="/trade">Trade</NavLink>
          <NavLink to="/positions">Positions</NavLink>
        </nav>
        <div style={{ marginTop: "2rem" }}>
          <p className="muted" style={{ fontSize: "0.85rem" }}>
            {user?.email}
          </p>
          <button className="secondary" type="button" onClick={() => void logout()}>
            Log out
          </button>
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <RequireAuth>
            <Shell>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/watchlist" element={<WatchlistPage />} />
                <Route path="/scanner" element={<ScannerPage />} />
                <Route path="/trade" element={<TradePage />} />
                <Route path="/positions" element={<PositionsPage />} />
              </Routes>
            </Shell>
          </RequireAuth>
        }
      />
    </Routes>
  );
}
