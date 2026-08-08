import { FormEvent, useEffect, useState } from "react";
import { api } from "../api";

type Profile = {
  risk_tolerance: string;
  investment_goals: string | null;
  max_position_pct: number;
  stop_loss_pct: number;
  take_profit_pct: number;
  portfolio_value: number;
};

export function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void api
      .getProfile()
      .then((r) => setProfile(r.profile as Profile))
      .catch((e) => setError(e.message));
  }, []);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    setMessage(null);
    setError(null);
    try {
      await api.putProfile(profile);
      setMessage("Profile saved");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    }
  };

  if (!profile) return <p className="muted">Loading profile…</p>;

  return (
    <div>
      <h2 className="page-title">Profile</h2>
      <p className="page-lead">Risk settings for paper trading.</p>
      <form className="panel" onSubmit={(e) => void onSubmit(e)}>
        <label htmlFor="risk">Risk tolerance</label>
        <select
          id="risk"
          value={profile.risk_tolerance}
          onChange={(e) =>
            setProfile({ ...profile, risk_tolerance: e.target.value })
          }
        >
          <option value="conservative">Conservative</option>
          <option value="moderate">Moderate</option>
          <option value="aggressive">Aggressive</option>
        </select>
        <label htmlFor="goals">Investment goals</label>
        <textarea
          id="goals"
          rows={3}
          value={profile.investment_goals || ""}
          onChange={(e) =>
            setProfile({ ...profile, investment_goals: e.target.value })
          }
        />
        <div className="grid-2">
          <div>
            <label htmlFor="maxpos">Max position %</label>
            <input
              id="maxpos"
              type="number"
              step="0.01"
              min="0.01"
              max="1"
              value={profile.max_position_pct}
              onChange={(e) =>
                setProfile({
                  ...profile,
                  max_position_pct: Number(e.target.value),
                })
              }
            />
          </div>
          <div>
            <label htmlFor="pv">Portfolio value</label>
            <input
              id="pv"
              type="number"
              value={profile.portfolio_value}
              onChange={(e) =>
                setProfile({
                  ...profile,
                  portfolio_value: Number(e.target.value),
                })
              }
            />
          </div>
        </div>
        {error && <p className="error">{error}</p>}
        {message && <p className="muted">{message}</p>}
        <button type="submit">Save</button>
      </form>
    </div>
  );
}
