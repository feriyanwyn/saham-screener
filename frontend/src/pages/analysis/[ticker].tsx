import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import {
  TrendingUp,
  TrendingDown,
  ShieldAlert,
  Bot,
  BrainCircuit,
  BarChart2,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Layers,
  Clock,
} from "lucide-react";
import { AppLayout } from "../../components/layout/AppLayout";
import { Card, CardHeader } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { TradingViewCandleChart } from "../../components/charts/TradingViewCandleChart";
import { AIAssistantChat } from "../../components/ai/AIAssistantChat";
import { apiService } from "../../services/api";
import { StockAnalysisBundle } from "../../types";
import { formatIDR, formatNumber, formatPercent } from "../../lib/utils";

export default function StockAnalysisPage() {
  const router = useRouter();
  const { ticker } = router.query;
  const currentTicker = (typeof ticker === "string" ? ticker : "BBCA").toUpperCase();

  const [data, setData] = useState<StockAnalysisBundle | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState("5m");

  useEffect(() => {
    if (!currentTicker) return;
    setLoading(true);
    apiService
      .getStockAnalysis(currentTicker, timeframe)
      .then((res) => setData(res))
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, [currentTicker, timeframe]);

  return (
    <AppLayout title={`${currentTicker} Analysis`}>
      <div className="space-y-6">
        {/* Top Header Card */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-[var(--card)] border border-[var(--border)]">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-blue-600 text-white font-bold text-lg flex items-center justify-center shadow-md shadow-blue-500/20 shrink-0">
              {currentTicker.slice(0, 2)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-[var(--text-primary)]">{currentTicker}</h1>
                <Badge variant={data?.signal.signal === "BUY" ? "buy" : "sell"}>
                  {data?.signal.signal || "NEUTRAL"}
                </Badge>
                {data?.quote.is_demo && <Badge variant="demo">DEMO</Badge>}
              </div>
              <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                Bursa Efek Indonesia • Papan Utama • Real-Time Scalping View
              </p>
            </div>
          </div>

          {/* Price & Bid/Ask Grid */}
          <div className="flex items-center gap-6">
            <div>
              <div className="text-xs text-[var(--text-secondary)]">Last Price</div>
              <div className="text-2xl font-bold font-mono text-[var(--text-primary)]">
                {data ? formatIDR(data.quote.last_price) : "..."}
              </div>
              <div
                className={`text-xs font-semibold font-mono flex items-center gap-1 ${
                  (data?.quote.change_pct || 0) >= 0 ? "text-emerald-500" : "text-rose-500"
                }`}
              >
                {(data?.quote.change_pct || 0) >= 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                {data ? formatPercent(data.quote.change_pct) : ""}
              </div>
            </div>

            <div className="hidden sm:block pl-6 border-l border-[var(--border)] font-mono text-xs space-y-1">
              <div>
                <span className="text-[var(--text-secondary)]">Bid: </span>
                <strong className="text-emerald-500">{data?.quote.bid || "-"}</strong>
              </div>
              <div>
                <span className="text-[var(--text-secondary)]">Ask: </span>
                <strong className="text-rose-500">{data?.quote.ask || "-"}</strong>
              </div>
              <div>
                <span className="text-[var(--text-secondary)]">Spread: </span>
                <strong>{data?.quote.spread_ticks || 1} tick</strong>
              </div>
            </div>
          </div>
        </div>

        {/* Candlestick & Volume Chart */}
        <div className="space-y-2">
          <TradingViewCandleChart
            candles={data?.candles || []}
            ticker={currentTicker}
            timeframe={timeframe}
            onTimeframeChange={(tf) => setTimeframe(tf.toLowerCase())}
            height={400}
          />
        </div>

        {/* 3 Pillars Grid: Deep Learning, Scalping Signal Engine, Technical Indicators */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Pillar 1: PyTorch Machine Learning (LSTM & BiLSTM) */}
          <Card>
            <CardHeader
              title="Machine Learning Models"
              subtitle="Walk-forward calibrated PyTorch inference"
              action={<BrainCircuit className="w-5 h-5 text-blue-500" />}
            />
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-[var(--background)] space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[var(--text-secondary)]">BiLSTM Directional Classifier</span>
                  <Badge variant={data?.machine_learning.bilstm_direction === "UP" ? "buy" : "sell"}>
                    {data?.machine_learning.bilstm_direction}
                  </Badge>
                </div>
                <div className="flex items-center justify-between font-mono text-xs font-bold">
                  <span>Up Probability:</span>
                  <span className="text-emerald-500">
                    {((data?.machine_learning.bilstm_up_prob || 0.72) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-[var(--border)] h-1.5 rounded-full overflow-hidden flex">
                  <div
                    className="bg-emerald-500 h-full"
                    style={{ width: `${(data?.machine_learning.bilstm_up_prob || 0.72) * 100}%` }}
                  />
                  <div
                    className="bg-rose-500 h-full"
                    style={{ width: `${(data?.machine_learning.bilstm_down_prob || 0.28) * 100}%` }}
                  />
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-[var(--background)] space-y-1.5 font-mono text-xs">
                <div className="text-[var(--text-secondary)] font-sans">LSTM Return Regressor</div>
                <div className="flex items-center justify-between">
                  <span>Expected Return:</span>
                  <strong className="text-emerald-500 font-bold">
                    +{data?.machine_learning.lstm_return_pred_pct || 0.85}%
                  </strong>
                </div>
                <div className="flex items-center justify-between">
                  <span>Target Price Est:</span>
                  <strong>{formatIDR(data?.machine_learning.lstm_expected_price || 0)}</strong>
                </div>
                <div className="flex items-center justify-between pt-1 border-t border-[var(--border)]">
                  <span>Model Confidence:</span>
                  <strong className="text-blue-500 font-bold">
                    {((data?.machine_learning.model_confidence || 0.81) * 100).toFixed(0)}%
                  </strong>
                </div>
              </div>
            </div>
          </Card>

          {/* Pillar 2: Scalping Decision Support Engine */}
          <Card>
            <CardHeader
              title="Scalping Decision Rules"
              subtitle="Tick-aligned entry, SL, TP & fee friction"
              action={<ShieldAlert className="w-5 h-5 text-emerald-500" />}
            />
            <div className="space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[var(--background)]">
                <span className="text-[var(--text-secondary)] font-sans">Entry Zone:</span>
                <strong className="text-[var(--text-primary)]">
                  {data?.signal.entry_zone ? `${data.signal.entry_zone[0]} - ${data.signal.entry_zone[1]}` : "-"}
                </strong>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[var(--background)]">
                <span className="text-[var(--text-secondary)] font-sans">Stop Loss:</span>
                <strong className="text-rose-500">{data?.signal.stop_loss || "-"}</strong>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[var(--background)]">
                <span className="text-[var(--text-secondary)] font-sans">Take Profit:</span>
                <strong className="text-emerald-500">{data?.signal.take_profit || "-"}</strong>
              </div>

              <div className="p-3 rounded-xl border border-blue-500/20 bg-blue-500/5 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[var(--text-secondary)] font-sans">Net Risk/Reward:</span>
                  <strong className="text-blue-500 font-bold">{data?.signal.net_risk_reward_ratio}x</strong>
                </div>
                <div className="flex items-center justify-between text-[11px] text-[var(--text-secondary)]">
                  <span className="font-sans">BEI Broker Fee:</span>
                  <span>~0.48% Round-trip</span>
                </div>
              </div>
            </div>
          </Card>

          {/* Pillar 3: Technical Indicators Grid */}
          <Card>
            <CardHeader
              title="Technical Indicators"
              subtitle="Vectorized intraday calculation"
              action={<BarChart2 className="w-5 h-5 text-purple-500" />}
            />
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="p-2.5 rounded-xl bg-[var(--background)]">
                <div className="text-[var(--text-secondary)] text-[10px] font-sans">RSI 14</div>
                <div className="font-bold text-sm text-[var(--text-primary)]">
                  {data?.technical_indicators.rsi_14.toFixed(1) || "-"}
                </div>
              </div>

              <div className="p-2.5 rounded-xl bg-[var(--background)]">
                <div className="text-[var(--text-secondary)] text-[10px] font-sans">Relative Volume</div>
                <div className="font-bold text-sm text-blue-500">
                  {data?.technical_indicators.relative_volume.toFixed(2)}x
                </div>
              </div>

              <div className="p-2.5 rounded-xl bg-[var(--background)]">
                <div className="text-[var(--text-secondary)] text-[10px] font-sans">Intraday VWAP</div>
                <div className="font-bold text-sm text-[var(--text-primary)]">
                  {data?.technical_indicators.vwap || "-"}
                </div>
              </div>

              <div className="p-2.5 rounded-xl bg-[var(--background)]">
                <div className="text-[var(--text-secondary)] text-[10px] font-sans">ATR 14</div>
                <div className="font-bold text-sm text-[var(--text-primary)]">
                  {data?.technical_indicators.atr_14 || "-"}
                </div>
              </div>

              <div className="p-2.5 rounded-xl bg-[var(--background)] col-span-2 flex items-center justify-between">
                <span className="text-[var(--text-secondary)] font-sans">EMA 20 / 50:</span>
                <span className="text-[var(--text-primary)]">
                  {data?.technical_indicators.ema_20} / {data?.technical_indicators.ema_50}
                </span>
              </div>
            </div>
          </Card>
        </div>

        {/* Embedded Interactive AI Copilot Assistant */}
        <div className="space-y-4">
          <AIAssistantChat initialTicker={currentTicker} />
        </div>
      </div>
    </AppLayout>
  );
}
