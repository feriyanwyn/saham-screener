import {
  MarketOverview,
  StockAnalysisBundle,
  ScreenerResult,
  AIDecisionResult,
  PortfolioSummary,
  BacktestResult,
} from "../types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

// Helper fetch wrapper with timeout
async function fetchWithTimeout(url: string, options: RequestInit = {}, timeoutMs = 12000): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    throw error;
  }
}

async function fetchJsonOrThrow<T>(url: string, options: RequestInit = {}, errorContext = "API"): Promise<T> {
  const res = await fetchWithTimeout(url, options);
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`${errorContext} failed (${res.status}): ${detail}`);
  }
  return (await res.json()) as T;
}

export const apiService = {
  // 1. Market Overview (Real-time IHSG & Top Movers, no DEMO fallback)
  async getMarketOverview(): Promise<MarketOverview> {
    return fetchJsonOrThrow<MarketOverview>(`${API_BASE_URL}/api/market/overview`, {}, "Market Overview");
  },

  // 2. Stock Screener (Real-time provider data)
  async runScreener(params: { minValue?: number; minRelVol?: number; maxSpread?: number } = {}): Promise<ScreenerResult[]> {
    const q = new URLSearchParams({
      min_rel_vol: String(params.minRelVol ?? 0),
    });
    const data = await fetchJsonOrThrow<{ results?: ScreenerResult[] }>(
      `${API_BASE_URL}/api/real-screener?${q.toString()}`,
      {},
      "Stock Screener"
    );
    return data.results || [];
  },

  // 3. Stock Comprehensive Analysis (Real historical OHLCV + Indicators)
  async getStockAnalysis(ticker: string, timeframe = "5m"): Promise<StockAnalysisBundle> {
    return fetchJsonOrThrow<StockAnalysisBundle>(
      `${API_BASE_URL}/api/analysis/${encodeURIComponent(ticker)}?timeframe=${encodeURIComponent(timeframe)}`,
      {},
      `Stock Analysis (${ticker})`
    );
  },

  // 4. AI Trading Decision Assistant
  async getAIDecision(ticker: string): Promise<AIDecisionResult> {
    return fetchJsonOrThrow<AIDecisionResult>(
      `${API_BASE_URL}/api/ai/decision/${encodeURIComponent(ticker)}`,
      {},
      `AI Decision (${ticker})`
    );
  },

  // 5. AI Chat Interaction
  async sendAIChat(query: string, tickerContext?: string): Promise<string> {
    const data = await fetchJsonOrThrow<{ reply: string }>(
      `${API_BASE_URL}/api/ai/chat`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, ticker_context: tickerContext }),
      },
      "AI Chat"
    );
    return data.reply;
  },

  // 6. Portfolio Summary
  async getPortfolio(): Promise<PortfolioSummary> {
    return fetchJsonOrThrow<PortfolioSummary>(`${API_BASE_URL}/api/portfolio`, {}, "Portfolio");
  },

  // 7. Backtest Runner
  async runBacktest(ticker: string, strategy = "Scalping_V1", capital = 10_000_000): Promise<BacktestResult> {
    return fetchJsonOrThrow<BacktestResult>(
      `${API_BASE_URL}/api/backtest/run`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker, strategy, initial_capital: capital }),
      },
      `Backtest (${ticker})`
    );
  },
};
