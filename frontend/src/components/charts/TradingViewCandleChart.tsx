import React, { useState } from "react";
import { CandleData } from "../../types";
import { formatIDR, formatNumber } from "../../lib/utils";

interface TradingViewCandleChartProps {
  candles: CandleData[];
  ticker: string;
  timeframe?: string;
  onTimeframeChange?: (tf: string) => void;
  height?: number;
}

export const TradingViewCandleChart: React.FC<TradingViewCandleChartProps> = ({
  candles,
  ticker,
  timeframe = "5M",
  onTimeframeChange,
  height = 380,
}) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  if (!candles || candles.length === 0) {
    return (
      <div
        className="w-full flex items-center justify-center text-sm text-[var(--text-secondary)] border border-dashed border-[var(--border)] rounded-xl"
        style={{ height }}
      >
        No candle data available for {ticker}
      </div>
    );
  }

  const timeframes = ["1M", "5M", "15M", "1H", "1D"];

  // Calculate scales
  const prices = candles.flatMap((c) => [c.high, c.low, c.ema20 || c.close, c.ema50 || c.close]);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice || 1;

  const volumes = candles.map((c) => c.volume);
  const maxVolume = Math.max(...volumes) || 1;

  const chartHeight = height - 100;
  const volumeHeight = 60;
  const paddingX = 40;
  const widthPerCandle = Math.max(12, 700 / candles.length);
  const totalWidth = Math.max(760, candles.length * widthPerCandle + paddingX * 2);

  const activeCandle = hoveredIndex !== null ? candles[hoveredIndex] : candles[candles.length - 1];

  const getY = (val: number) => {
    return chartHeight - ((val - minPrice) / priceRange) * (chartHeight - 30) + 15;
  };

  const getVolY = (vol: number) => {
    return height - (vol / maxVolume) * volumeHeight - 10;
  };

  // EMA lines points
  const ema20Points = candles
    .map((c, i) => (c.ema20 ? `${paddingX + i * widthPerCandle},${getY(c.ema20)}` : null))
    .filter(Boolean)
    .join(" ");

  const ema50Points = candles
    .map((c, i) => (c.ema50 ? `${paddingX + i * widthPerCandle},${getY(c.ema50)}` : null))
    .filter(Boolean)
    .join(" ");

  return (
    <div className="w-full flex flex-col bg-[var(--card)] rounded-xl border border-[var(--border)] overflow-hidden">
      {/* Chart Top Bar: Info & Timeframe */}
      <div className="flex flex-wrap items-center justify-between px-4 py-2.5 border-b border-[var(--border)] bg-[var(--background)]/40 gap-3">
        <div className="flex items-center gap-4 text-xs font-mono">
          <span className="font-bold text-sm text-[var(--text-primary)]">{ticker}</span>
          <span className="text-[var(--text-secondary)]">
            O: <strong className="text-[var(--text-primary)]">{formatIDR(activeCandle.open)}</strong>
          </span>
          <span className="text-[var(--text-secondary)]">
            H: <strong className="text-emerald-500">{formatIDR(activeCandle.high)}</strong>
          </span>
          <span className="text-[var(--text-secondary)]">
            L: <strong className="text-rose-500">{formatIDR(activeCandle.low)}</strong>
          </span>
          <span className="text-[var(--text-secondary)]">
            C: <strong className="text-[var(--text-primary)]">{formatIDR(activeCandle.close)}</strong>
          </span>
          <span className="text-[var(--text-secondary)] hidden sm:inline">
            Vol: <strong className="text-[var(--text-primary)]">{formatNumber(activeCandle.volume, 0)}</strong>
          </span>
        </div>

        {/* EMA Legend & Timeframes */}
        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2 text-[11px] font-medium">
            <span className="flex items-center gap-1 text-amber-500">
              <span className="w-2 h-0.5 bg-amber-500" /> EMA 20
            </span>
            <span className="flex items-center gap-1 text-blue-500">
              <span className="w-2 h-0.5 bg-blue-500" /> EMA 50
            </span>
          </div>

          <div className="flex items-center rounded-lg bg-[var(--card)] border border-[var(--border)] p-0.5 text-xs font-semibold">
            {timeframes.map((tf) => (
              <button
                key={tf}
                onClick={() => onTimeframeChange && onTimeframeChange(tf)}
                className={`px-2 py-1 rounded-md transition-colors ${
                  timeframe === tf
                    ? "bg-blue-600 text-white shadow-xs"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* SVG Candlestick & Volume Chart */}
      <div className="w-full overflow-x-auto relative">
        <svg
          viewBox={`0 0 ${totalWidth} ${height}`}
          className="w-full min-w-[700px] h-[380px] select-none"
          onMouseLeave={() => setHoveredIndex(null)}
        >
          {/* Grid lines */}
          {[0.2, 0.4, 0.6, 0.8].map((pct, idx) => {
            const y = chartHeight * pct;
            const priceLabel = Math.round(maxPrice - pct * priceRange);
            return (
              <g key={idx}>
                <line
                  x1="0"
                  y1={y}
                  x2={totalWidth}
                  y2={y}
                  stroke="currentColor"
                  className="text-[var(--border)]"
                  strokeDasharray="4 4"
                  strokeWidth="0.8"
                />
                <text
                  x={totalWidth - 10}
                  y={y - 4}
                  textAnchor="end"
                  className="fill-[var(--text-secondary)] text-[10px] font-mono"
                >
                  {formatIDR(priceLabel)}
                </text>
              </g>
            );
          })}

          {/* Volume separator */}
          <line
            x1="0"
            y1={chartHeight + 10}
            x2={totalWidth}
            y2={chartHeight + 10}
            stroke="currentColor"
            className="text-[var(--border)]"
            strokeWidth="1"
          />

          {/* Candlesticks & Volume Bars */}
          {candles.map((c, i) => {
            const x = paddingX + i * widthPerCandle;
            const isBull = c.close >= c.open;
            const candleColor = isBull ? "#10B981" : "#EF4444";
            const top = Math.min(getY(c.open), getY(c.close));
            const bodyHeight = Math.max(2, Math.abs(getY(c.open) - getY(c.close)));
            const volY = getVolY(c.volume);
            const volHeight = height - volY - 10;
            const barWidth = Math.max(4, widthPerCandle * 0.65);

            return (
              <g
                key={i}
                className="cursor-crosshair group"
                onMouseEnter={() => setHoveredIndex(i)}
              >
                {/* Candle Wick */}
                <line
                  x1={x}
                  y1={getY(c.high)}
                  x2={x}
                  y2={getY(c.low)}
                  stroke={candleColor}
                  strokeWidth="1.2"
                />

                {/* Candle Body */}
                <rect
                  x={x - barWidth / 2}
                  y={top}
                  width={barWidth}
                  height={bodyHeight}
                  fill={candleColor}
                  rx="1"
                />

                {/* Volume Bar */}
                <rect
                  x={x - barWidth / 2}
                  y={volY}
                  width={barWidth}
                  height={volHeight}
                  fill={candleColor}
                  opacity={hoveredIndex === i ? 0.9 : 0.4}
                />

                {/* Hover line */}
                {hoveredIndex === i && (
                  <line
                    x1={x}
                    y1={0}
                    x2={x}
                    y2={height}
                    stroke="currentColor"
                    className="text-blue-500/40"
                    strokeDasharray="2 2"
                    strokeWidth="1"
                  />
                )}
              </g>
            );
          })}

          {/* EMA Overlays */}
          {ema20Points && (
            <polyline
              points={ema20Points}
              fill="none"
              stroke="#F59E0B"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          )}
          {ema50Points && (
            <polyline
              points={ema50Points}
              fill="none"
              stroke="#3B82F6"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          )}
        </svg>
      </div>
    </div>
  );
};
