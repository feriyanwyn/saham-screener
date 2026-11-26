import React, { useState } from "react";
import {
  History,
  Play,
  RotateCcw,
  TrendingUp,
  Percent,
  BarChart3,
  ShieldAlert,
  ArrowRight,
} from "lucide-react";
import { AppLayout } from "../components/layout/AppLayout";
import { Card, CardHeader } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { EquityCurveChart } from "../components/charts/EquityCurveChart";
import { apiService } from "../services/api";
import { BacktestResult } from "../types";
import { formatIDR, formatNumber, formatPercent } from "../lib/utils";

export default function BacktestingPage() {
  const [ticker, setTicker] = useState("BBCA");
  const [strategy, setStrategy] = useState("Scalping_V1");
  const [capital, setCapital] = useState(10_000_000);
  const [slippage, setSlippage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);

  const runSimulation = async () => {
    setLoading(true);
    try {
      const res = await apiService.runBacktest(ticker, strategy, capital);
      setResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout title="Walk-Forward Backtesting">
      <div className="space-y-6">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
              Walk-Forward Backtesting Engine
            </h1>
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Pengujian strategi kuantitatif intraday candle demi candle tanpa look-ahead bias
            </p>
          </div>

          <Button onClick={runSimulation} disabled={loading}>
            <Play className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Run Simulation
          </Button>
        </div>

        {/* Backtest Parameters Toolbar */}
        <Card className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                Stock Ticker
              </label>
              <select
                value={ticker}
                onChange={(e) => setTicker(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl bg-[var(--background)] border border-[var(--border)] font-bold uppercase focus:outline-none"
              >
                {["BBCA", "MEDC", "ADRO", "TLKM", "ASII", "BRIS"].map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                Quantitative Strategy
              </label>
              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl bg-[var(--background)] border border-[var(--border)] font-medium focus:outline-none"
              >
                <option value="Scalping_V1">Scalping V1 (VWAP + RelVol + BiLSTM)</option>
                <option value="Momentum_Breakout">EMA 20 Breakout & RSI Confluence</option>
                <option value="Mean_Reversion">Bollinger Band Extreme Reversion</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                Initial Capital (IDR)
              </label>
              <input
                type="number"
                step="5000000"
                value={capital}
                onChange={(e) => setCapital(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs rounded-xl bg-[var(--background)] border border-[var(--border)] font-mono font-bold"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                Execution Slippage
              </label>
              <select
                value={slippage}
                onChange={(e) => setSlippage(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs rounded-xl bg-[var(--background)] border border-[var(--border)] font-mono focus:outline-none"
              >
                <option value={0}>0 Tick (Ideal)</option>
                <option value={1}>1 Tick (Realistic BEI)</option>
                <option value={2}>2 Ticks (High Volatility)</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Results Section */}
        {result ? (
          <div className="space-y-6">
            {/* 4 Performance Metric Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <div className="text-xs text-[var(--text-secondary)] mb-1">Net Profit / Loss</div>
                <div className="text-2xl font-bold font-mono text-emerald-500">
                  +{formatIDR(result.net_profit_idr)}
                </div>
                <div className="text-xs font-semibold text-emerald-500 mt-2 font-mono">
                  {formatPercent(result.net_profit_pct)} Total Return
                </div>
              </Card>

              <Card>
                <div className="text-xs text-[var(--text-secondary)] mb-1">Win Rate %</div>
                <div className="text-2xl font-bold font-mono text-blue-500">
                  {result.win_rate_pct.toFixed(1)}%
                </div>
                <div className="text-xs text-[var(--text-secondary)] mt-2">
                  {result.winning_trades} Win / {result.losing_trades} Loss ({result.total_trades} trades)
                </div>
              </Card>

              <Card>
                <div className="text-xs text-[var(--text-secondary)] mb-1">Profit Factor</div>
                <div className="text-2xl font-bold font-mono text-[var(--text-primary)]">
                  {result.profit_factor.toFixed(2)}
                </div>
                <div className="text-xs text-[var(--text-secondary)] mt-2">Gross Win / Gross Loss</div>
              </Card>

              <Card>
                <div className="text-xs text-[var(--text-secondary)] mb-1">Max Drawdown</div>
                <div className="text-2xl font-bold font-mono text-rose-500">
                  -{result.max_drawdown_pct.toFixed(1)}%
                </div>
                <div className="text-xs text-[var(--text-secondary)] mt-2 font-mono">
                  {formatIDR(result.max_drawdown_idr)} peak-to-trough
                </div>
              </Card>
            </div>

            {/* Equity Curve Chart */}
            <EquityCurveChart
              data={result.equity_curve}
              initialCapital={result.initial_capital}
              height={260}
            />

            {/* Trade Logs Table */}
            <Card className="p-0 overflow-hidden">
              <div className="p-4 border-b border-[var(--border)] flex justify-between items-center">
                <div>
                  <h3 className="font-semibold text-sm text-[var(--text-primary)]">Trade Execution Ledger</h3>
                  <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                    Candle t signal &bull; Candle t+1 execution &bull; Broker fees deducted
                  </p>
                </div>
                <span className="text-xs font-mono text-[var(--text-secondary)]">
                  Fees Paid: <strong>{formatIDR(result.total_fees_paid)}</strong>
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--border)] bg-[var(--background)]/60 text-[var(--text-secondary)] font-semibold">
                      <th className="py-3 px-4">#</th>
                      <th className="py-3 px-4">Entry Time</th>
                      <th className="py-3 px-4">Exit Time</th>
                      <th className="py-3 px-4 text-right">Entry Price</th>
                      <th className="py-3 px-4 text-right">Exit Price</th>
                      <th className="py-3 px-4 text-right">Lots</th>
                      <th className="py-3 px-4 text-right">Net P&L</th>
                      <th className="py-3 px-4 text-center">Exit Trigger</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border)] font-mono">
                    {result.trade_logs.map((tr) => (
                      <tr key={tr.trade_id} className="hover:bg-[var(--background)]/40">
                        <td className="py-3 px-4 text-[var(--text-secondary)]">{tr.trade_id}</td>
                        <td className="py-3 px-4">{tr.entry_time}</td>
                        <td className="py-3 px-4">{tr.exit_time}</td>
                        <td className="py-3 px-4 text-right">{formatIDR(tr.entry_price)}</td>
                        <td className="py-3 px-4 text-right">{formatIDR(tr.exit_price)}</td>
                        <td className="py-3 px-4 text-right">{tr.lots} lot</td>
                        <td className="py-3 px-4 text-right font-bold">
                          <span className={tr.net_pnl >= 0 ? "text-emerald-500" : "text-rose-500"}>
                            {tr.net_pnl >= 0 ? "+" : ""}
                            {formatIDR(tr.net_pnl)} ({formatPercent(tr.return_pct)})
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <Badge variant={tr.exit_reason === "TAKE_PROFIT" ? "buy" : "sell"}>
                            {tr.exit_reason}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        ) : (
          <Card className="py-16 text-center text-[var(--text-secondary)] space-y-3">
            <History className="w-10 h-10 mx-auto text-blue-500/40" />
            <h3 className="font-bold text-sm text-[var(--text-primary)]">Belum Ada Simulasi Berjalan</h3>
            <p className="text-xs max-w-md mx-auto">
              Pilih ticker dan strategi di atas, kemudian klik <strong>Run Simulation</strong> untuk memproses candle intraday historis.
            </p>
          </Card>
        )}
      </div>
    </AppLayout>
  );
}
