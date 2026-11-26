import React from "react";
import { PortfolioPosition } from "../../types";
import { formatPercent } from "../../lib/utils";

interface PortfolioAllocationChartProps {
  positions: PortfolioPosition[];
}

export const PortfolioAllocationChart: React.FC<PortfolioAllocationChartProps> = ({ positions }) => {
  if (!positions || positions.length === 0) {
    return (
      <div className="h-44 flex items-center justify-center text-xs text-[var(--text-secondary)]">
        No active positions in portfolio
      </div>
    );
  }

  const colors = ["#2563EB", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#06B6D4"];

  return (
    <div className="flex flex-col gap-4">
      {/* Progress bar visual */}
      <div className="h-4 w-full rounded-full overflow-hidden flex bg-[var(--muted)]">
        {positions.map((pos, idx) => (
          <div
            key={pos.ticker}
            style={{
              width: `${pos.allocation_pct}%`,
              backgroundColor: colors[idx % colors.length],
            }}
            title={`${pos.ticker}: ${pos.allocation_pct}%`}
            className="h-full transition-all duration-300"
          />
        ))}
      </div>

      {/* Legend list */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        {positions.map((pos, idx) => (
          <div key={pos.ticker} className="flex items-center justify-between p-2 rounded-lg bg-[var(--background)]">
            <div className="flex items-center gap-2">
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: colors[idx % colors.length] }}
              />
              <span className="font-bold text-[var(--text-primary)]">{pos.ticker}</span>
            </div>
            <span className="font-mono text-[var(--text-secondary)]">
              {formatPercent(pos.allocation_pct).replace("+", "")}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
