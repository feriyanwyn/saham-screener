// TypeScript Definitions for AI Stock Analyzer (BEI / IDX)

export type Theme = "light" | "dark" | "system";

export type SignalType = "BUY" | "SELL" | "HOLD" | "WATCHLIST";

export type ListingBoard = "Utama" | "Pengembangan" | "Akselerasi" | "Ekonomi Baru";

export type StockStatus = "ACTIVE" | "SUSPENDED" | "NEWLY_LISTED" | "DELISTED";

export interface Instrument {
  ticker: string;
  name: string;
  sector: string;
  subsector?: string;
  industry?: string;
  board: ListingBoard;
  shares_outstanding?: number;
  market_cap?: number;
  listing_date?: string;
  status: StockStatus;
  is_active: boolean;
  is_suspended: boolean;
  has_daily_data?: boolean;
  has_intraday_data?: boolean;
}

export interface LiveQuote {
  ticker: string;
  name?: string;
  last_price: number;
  close: number;
  open: number;
  high: number;
  low: number;
  previous_close: number;
  change: number;
  change_pct: number;
  volume: number;
  value: number;
  frequency?: number;
  bid: number;
  bid_volume?: number;
  ask: number;
  ask_volume?: number;
  spread_ticks?: number;
  is_ara?: boolean;
  is_arb?: boolean;
  timestamp: string;
  is_demo?: boolean;
}

export interface CandleData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ema20?: number;
  ema50?: number;
  ema200?: number;
  vwap?: number;
}

export interface TechnicalIndicators {
  close: number;
  rsi_14: number;
  macd: number;
  macd_signal: number;
  macd_hist: number;
  ema_9: number;
  ema_20: number;
  ema_50: number;
  ema_200?: number;
  vwap: number;
  atr_14: number;
  relative_volume: number;
  bb_upper?: number;
  bb_middle?: number;
  bb_lower?: number;
  golden_cross?: boolean;
  death_cross?: boolean;
  macd_bullish_cross?: boolean;
  macd_bearish_cross?: boolean;
}

export interface MLPrediction {
  lstm_return_pred_pct: number;
  lstm_expected_price: number;
  bilstm_up_prob: number;
  bilstm_down_prob: number;
  bilstm_direction: "UP" | "DOWN";
  model_confidence: number;
  timestamp: string;
}

export interface ScalpingSignal {
  ticker: string;
  signal: SignalType;
  confidence: number;
  entry_zone: [number, number];
  stop_loss: number;
  take_profit: number;
  risk_reward_ratio: number;
  estimated_cost_pct: number;
  net_risk_reward_ratio: number;
  reasons: string[];
  invalidation_criteria: string[];
  is_ara_near: boolean;
  timestamp: string;
}

export interface StockAnalysisBundle {
  ticker: string;
  quote: LiveQuote;
  timeframe: string;
  candles: CandleData[];
  technical_indicators: TechnicalIndicators;
  machine_learning: MLPrediction;
  signal: ScalpingSignal;
  updated_at: string;
}

export interface MarketOverview {
  ihsg: {
    name: string;
    price: number;
    change: number;
    change_pct: number;
    status: "OPEN" | "CLOSED";
  };
  market_stats: {
    total_turnover_idr: number;
    monitored_stocks: number;
    gainers_count: number;
    losers_count: number;
    unchanged_count: number;
  };
  top_gainers: LiveQuote[];
  top_losers: LiveQuote[];
  ai_insight_preview: string;
  updated_at: string;
}

export interface ScreenerResult {
  ticker: string;
  name: string;
  sector: string;
  last_price: number;
  change_pct: number;
  volume: number;
  value_idr: number;
  relative_volume: number;
  rsi_14: number;
  macd_status: string;
  signal: SignalType;
  scalping_score: number;
  spread_ticks: number;
}

export interface AIDecisionResult {
  stock_ticker: string;
  analysis_timestamp: string;
  decision: "BUY" | "SELL" | "HOLD" | "NO TRADE";
  validation_status: "PASSED" | "REJECTED";
  rejection_reason?: string;
  trend_analysis: string;
  technical_analysis: string;
  ml_prediction_interpretation: string;
  entry_zone: [number, number];
  stop_loss: number;
  take_profit: number;
  risk_reward_ratio: number;
  estimated_transaction_cost_pct: number;
  net_risk_reward_ratio: number;
  main_risks: string[];
  invalidation_conditions: string[];
  confidence_assessment: "HIGH" | "MEDIUM" | "LOW";
  detailed_explanation: string;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  content: string;
  timestamp: string;
  cards?: {
    ticker?: string;
    decision?: string;
    confidence?: string;
    risk_reward?: number;
  };
}

export interface PortfolioPosition {
  ticker: string;
  shares: number;
  lots: number;
  avg_buy_price: number;
  current_price: number;
  cost_basis: number;
  current_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  allocation_pct: number;
}

export interface PortfolioSummary {
  account_id: string;
  initial_capital: number;
  cash_balance: number;
  portfolio_value: number;
  total_equity: number;
  total_pnl: number;
  total_pnl_pct: number;
  win_rate_pct: number;
  open_positions: PortfolioPosition[];
  trade_history: Array<{
    id: number;
    ticker: string;
    order_type: "BUY" | "SELL";
    lots: number;
    execution_price: number;
    gross_amount: number;
    net_amount: number;
    fee_amount: number;
    executed_at: string;
  }>;
}

export interface BacktestResult {
  ticker: string;
  strategy_name: string;
  initial_capital: number;
  final_equity: number;
  net_profit_idr: number;
  net_profit_pct: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  profit_factor: number;
  max_drawdown_idr: number;
  max_drawdown_pct: number;
  total_fees_paid: number;
  equity_curve: Array<{
    timestamp: string;
    equity: number;
    cash: number;
    drawdown_pct: number;
  }>;
  trade_logs: Array<{
    trade_id: number;
    entry_time: string;
    exit_time: string;
    entry_price: number;
    exit_price: number;
    lots: number;
    gross_pnl: number;
    net_pnl: number;
    return_pct: number;
    exit_reason: string;
  }>;
}

export interface NotificationAlert {
  id: string;
  type: "PRICE" | "SIGNAL" | "WATCHLIST" | "MODEL";
  title: string;
  message: string;
  ticker?: string;
  timestamp: string;
  is_read: boolean;
  priority: "HIGH" | "NORMAL" | "LOW";
}
