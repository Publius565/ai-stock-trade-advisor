export interface Env {
  DB: D1Database;
  ASSETS: Fetcher;
  APP_ID: string;
  SESSION_TTL_SECONDS: string;
  SESSION_SECRET?: string;
  ALPACA_API_KEY?: string;
  ALPACA_SECRET_KEY?: string;
  ALPACA_BASE_URL?: string;
  ALPHA_VANTAGE_API_KEY?: string;
}

export type MembershipPermissions = {
  paper_trade?: boolean;
  ml?: boolean;
  [key: string]: boolean | undefined;
};

export type AuthUser = {
  id: string;
  email: string;
  name: string | null;
  role: string;
  permissions: MembershipPermissions;
};

export type TradeProfile = {
  user_id: string;
  risk_tolerance: "conservative" | "moderate" | "aggressive";
  investment_goals: string | null;
  max_position_pct: number;
  stop_loss_pct: number;
  take_profit_pct: number;
  portfolio_value: number;
};

export type Watchlist = {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  is_default: number;
  symbols?: WatchlistSymbol[];
};

export type WatchlistSymbol = {
  id: string;
  watchlist_id: string;
  symbol: string;
  notes: string | null;
};

export type OrderSide = "buy" | "sell";
export type OrderType = "market" | "limit";
export type OrderStatus =
  | "pending"
  | "submitted"
  | "filled"
  | "cancelled"
  | "rejected";

export type TradeOrder = {
  id: string;
  user_id: string;
  symbol: string;
  side: OrderSide;
  order_type: OrderType;
  quantity: number;
  limit_price: number | null;
  status: OrderStatus;
  broker: string;
  broker_order_id: string | null;
  filled_price: number | null;
  filled_at: number | null;
  created_at: number;
};

export type TradePosition = {
  id: string;
  user_id: string;
  symbol: string;
  quantity: number;
  avg_entry_price: number;
  current_price: number | null;
};

export type BrokerAccount = {
  broker: string;
  connected: boolean;
  account_id?: string;
  status?: string;
  buying_power?: number;
  cash?: number;
  portfolio_value?: number;
  equity?: number;
};

export type Mover = {
  symbol: string;
  change_pct: number;
  price: number;
  volume: number;
};
