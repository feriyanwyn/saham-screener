import React from "react";
import { formatIDR, formatNumber } from "../../lib/utils";

interface EquityPoint {
  timestamp: string;
  equity: number;
  drawdown_pct?: number;
}

interface EquityCurveChartProps {
  data: EquityPoint[];
  initialCapital?: number;
  height?: number;
}

export const EquityCurveChart: React.FC<EquityCurveChartProps> = ({
  data,
  initialCapital = 10_000_000,
  height = 240,
}) => {
  if (!data || data.length === 0) {
    return (
      <div
        className="w-full flex items-center justify-center text-xs text-[var(--text-secondary)] border border-dashed border-[var(--border)] rounded-xl"
        style={{ height }}
      >
        No backtest simulation data yet
      </div>
    );
  }

  const values = data.map((d) => d.equity);
  const minEquity = Math.min(...values, initialCapital * 0.95);
  const maxEquity = Math.max(...values, initialCapital * 1.05);
  const range = maxEquity - minEquity || 1;

  const totalWidth = 600;
  const paddingY = 20;
  const chartH = height - paddingY * 2;

  const points = data.map((d, i) => {
    const x = (i / (data.length - 1 || 1)) * (totalWidth - 40) + 20;
    const y = chartH - ((d.equity - minEquity) / range) * chartH + paddingY;
    return `${x},${y}`;
  });

  const polylineStr = points.join(" ");
  const areaPoints = `20,${height} ${polylineStr} ${totalWidth - 20},${height}`;

  const finalEquity = data[data.length - 1].equity;
  const isProfitable = finalEquity >= initialCapital;
  const strokeColor = isProfitable ? "#10B981" : "#EF4444";
  const gradientId = `eq-grad-${isProfitable ? "green" : "red"}`;

  return (
    <div className="w-full bg-[var(--card)] rounded-xl border border-[var(--border)] p-4 flex flex-col gap-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-[var(--text-secondary)] font-medium">Equity Growth Curve</span>
        <span className="font-mono font-bold text-[var(--text-primary)]">
          {formatIDR(finalEquity)}
        </span>
      </div>

      <div className="w-full overflow-hidden">
        <svg viewBox={`0 0 ${totalWidth} ${height}`} className="w-full h-[220px]">
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={strokeColor} stopOpacity="0.3" />
              <stop offset="100%" stopColor={strokeColor} stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Baseline Initial Capital */}
          <line
            x1="20"
            y1={chartH - ((initialCapital - minEquity) / range) * chartH + paddingY}
            x2={totalWidth - 20}
            y2={chartH - ((initialCapital - minEquity) / range) * chartH + paddingY}
            stroke="#64748B"
            strokeDasharray="4 4"
            strokeWidth="1"
            opacity="0.6"
          />

          {/* Area under curve */}
          <polygon points={areaPoints} fill={`url(#${gradientId})`} />

          {/* Line curve */}
          <polyline
            points={polylineStr}
            fill="none"
            stroke={strokeColor}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    </div>
  );
};
