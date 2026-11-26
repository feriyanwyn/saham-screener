import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Bot,
  ArrowRight,
  ShieldAlert,
  Sparkles,
  RefreshCw,
  Wallet,
} from "lucide-react";
import { AppLayout } from "../components/layout/AppLayout";
import { Card, CardHeader } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Skeleton } from "../components/ui/Skeleton";
import { TradingViewCandleChart } from "../components/charts/TradingViewCandleChart";
import { apiService } from "../services/api";
import { MarketOverview, PortfolioSummary, CandleData } from "../types";
import { formatIDR, formatNumber, formatPercent } from "../lib/utils";

export default function DashboardPage() {
  const [overview, setOverview] = useState<MarketOverview | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [previewCandles, setPreviewCandles] = useState<CandleData[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [mkt, port, analysis] = await Promise.all([
        apiService.getMarketOverview(),
        apiService.getPortfolio(),
        apiService.getStockAnalysis("BBCA", "5m"),
      ]);
      setOverview(mkt);
      setPortfolio(port);
      setPreviewCandles(analysis.candles);
    } catch (e) {
      console.error("Failed to load dashboard data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <AppLayout title="Dashboard">
      <div className="space-y-6">
        {/* Top Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
              Market Dashboard
            </h1>
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Bursa Efek Indonesia (IDX) Scalping & Machine Learning Overview
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-[var(--text-secondary)] font-mono">
              Updated: {overview?.updated_at || "Live"}
            </span>
            <Button variant="outline" size="sm" onClick={loadData} disabled={loading}>
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* AI Market Insight Card */}
        <Card className="bg-gradient-to-r from-blue-600/10 via-indigo-600/10 to-transparent border-blue-500/20">
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-sm shadow-blue-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="flex-1 space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-[var(--text-primary)]">AI Market Intelligence</span>
                <Badge variant="primary">Copilot</Badge>
              </div>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                {overview?.ai_insight_preview ||
                  "IHSG bergerak konsolidasi dengan rotasi likuiditas ke sektor perbankan dan energi. Waspadai volatilitas menjelang penutupan sesi."}
              </p>
            </div>
            <Link href="/ai-assistant">
              <Button size="sm" variant="ghost" className="text-blue-500">
                Ask Copilot <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </Link>
          </div>
        </Card>

        {/* 4 Summary Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* IHSG Card */}
          <Card>
            <div className="flex items-center justify-between text-xs text-[var(--text-secondary)] mb-1">
              <span>IHSG Composite</span>
              <Badge variant="buy">OPEN</Badge>
            </div>
            <div className="text-2xl font-bold font-tabular text-[var(--text-primary)]">
              {overview?.ihsg.price ? formatNumber(overview.ihsg.price, 2) : "7,285.50"}
            </div>
            <div className="flex items-center gap-1.5 mt-2 text-xs font-semibold text-emerald-500">
              <TrendingUp className="w-4 h-4" />
              <span>+{overview?.ihsg.change_pct || 0.45}%</span>
              <span className="text-[var(--text-secondary)] font-normal font-mono">
                (+{overview?.ihsg.change || 32.8})
              </span>
            </div>
          </Card>

          {/* Market Turnover */}
          <Card>
            <div className="flex items-center justify-between text-xs text-[var(--text-secondary)] mb-1">
              <span>Total Turnover (IDR)</span>
              <BarChart3 className="w-4 h-4 text-blue-500" />
            </div>
            <div className="text-2xl font-bold font-tabular text-[var(--text-primary)]">
              {overview?.market_stats.total_turnover_idr
                ? `Rp ${(overview.market_stats.total_turnover_idr / 1e12).toFixed(2)} T`
                : "Rp 12.45 T"}
            </div>
            <p className="text-xs text-[var(--text-secondary)] mt-2">
              From {overview?.market_stats.monitored_stocks || 924} listed stocks
            </p>
          </Card>

          {/* Market Breadth */}
          <Card>
            <div className="flex items-center justify-between text-xs text-[var(--text-secondary)] mb-1">
              <span>Market Breadth</span>
              <Activity className="w-4 h-4 text-amber-500" />
            </div>
            <div className="flex items-center gap-3 mt-1">
              <div className="flex items-center gap-1 text-emerald-500 text-lg font-bold font-tabular">
                <TrendingUp className="w-4 h-4" />
                {overview?.market_stats.gainers_count || 285}
              </div>
              <div className="flex items-center gap-1 text-rose-500 text-lg font-bold font-tabular">
                <TrendingDown className="w-4 h-4" />
                {overview?.market_stats.losers_count || 210}
              </div>
              <div className="text-xs text-[var(--text-secondary)]">
                ({overview?.market_stats.unchanged_count || 140} Flat)
              </div>
            </div>
            <div className="w-full bg-[var(--muted)] h-1.5 rounded-full mt-3 overflow-hidden flex">
              <div className="bg-emerald-500 h-full w-[55%]" />
              <div className="bg-rose-500 h-full w-[45%]" />
            </div>
          </Card>

          {/* Paper Portfolio Summary */}
          <Card>
            <div className="flex items-center justify-between text-xs text-[var(--text-secondary)] mb-1">
              <span>Virtual Portfolio</span>
              <Wallet className="w-4 h-4 text-purple-500" />
            </div>
            <div className="text-2xl font-bold font-tabular text-[var(--text-primary)]">
              {portfolio ? formatIDR(portfolio.total_equity) : "Rp 50,900,000"}
            </div>
            <div className="flex items-center justify-between mt-2 text-xs">
              <span className="text-emerald-500 font-semibold font-tabular">
                +{portfolio?.total_pnl_pct || 1.8}% P&L
              </span>
              <Link href="/portfolio" className="text-blue-500 hover:underline">
                View Positions →
              </Link>
            </div>
          </Card>
        </div>

        {/* Main Chart + Top Gainers/Losers Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Candlestick Chart (2 Cols) */}
          <div className="lg:col-span-2 space-y-4">
            <CardHeader
              title="Market Trend: BBCA (Intraday 5M)"
              subtitle="PyTorch Deep Learning & Technical Overlay Preview"
              action={
                <Link href="/analysis/BBCA">
                  <Button size="sm" variant="outline">
                    Full Analysis <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                </Link>
              }
            />
            <TradingViewCandleChart candles={previewCandles} ticker="BBCA" timeframe="5M" height={360} />
          </div>

          {/* Top Gainers & Losers (1 Col) */}
          <div className="space-y-4">
            <Card>
              <CardHeader title="Top Scalping Gainers" subtitle="Highest price momentum" />
              <div className="space-y-2">
                {overview?.top_gainers.map((g) => (
                  <Link
                    key={g.ticker}
                    href={`/analysis/${g.ticker}`}
                    className="flex items-center justify-between p-2.5 rounded-xl hover:bg-[var(--background)] transition-colors border border-transparent hover:border-[var(--border)]"
                  >
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="font-bold text-sm text-[var(--text-primary)]">{g.ticker}</span>
                        {g.is_demo && <Badge variant="demo">DEMO</Badge>}
                      </div>
                      <span className="text-[11px] text-[var(--text-secondary)] font-mono">
                        {formatIDR(g.last_price)}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-bold text-emerald-500 font-mono block">
                        +{g.change_pct}%
                      </span>
                      <span className="text-[10px] text-[var(--text-secondary)]">Vol {formatNumber(g.volume / 1e6, 1)}M</span>
                    </div>
                  </Link>
                ))}
              </div>
            </Card>

            <Card>
              <CardHeader title="Top Market Losers" subtitle="Intraday pullback pressure" />
              <div className="space-y-2">
                {overview?.top_losers.map((l) => (
                  <Link
                    key={l.ticker}
                    href={`/analysis/${l.ticker}`}
                    className="flex items-center justify-between p-2.5 rounded-xl hover:bg-[var(--background)] transition-colors border border-transparent hover:border-[var(--border)]"
                  >
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="font-bold text-sm text-[var(--text-primary)]">{l.ticker}</span>
                        {l.is_demo && <Badge variant="demo">DEMO</Badge>}
                      </div>
                      <span className="text-[11px] text-[var(--text-secondary)] font-mono">
                        {formatIDR(l.last_price)}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-bold text-rose-500 font-mono block">
                        {l.change_pct}%
                      </span>
                      <span className="text-[10px] text-[var(--text-secondary)]">Vol {formatNumber(l.volume / 1e6, 1)}M</span>
                    </div>
                  </Link>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
