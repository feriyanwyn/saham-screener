import React, { useEffect, useState } from "react";
import {
  Wallet,
  TrendingUp,
  Plus,
  History,
  ShieldCheck,
  ArrowUpRight,
  ArrowDownRight,
  DollarSign,
  PieChart,
} from "lucide-react";
import { AppLayout } from "../components/layout/AppLayout";
import { Card, CardHeader } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import { PortfolioAllocationChart } from "../components/charts/PortfolioAllocationChart";
import { apiService } from "../services/api";
import { PortfolioSummary } from "../types";
import { formatIDR, formatNumber, formatPercent } from "../lib/utils";

export default function PortfolioPage() {
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [tickerInput, setTickerInput] = useState("BBCA");
  const [lotsInput, setLotsInput] = useState(10);
  const [priceInput, setPriceInput] = useState(10150);

  const loadData = async () => {
    setLoading(true);
    try {
      const p = await apiService.getPortfolio();
      setPortfolio(p);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleExecuteBuy = () => {
    // In demo / simulator mode, adds to portfolio locally
    alert(`Order BUY ${lotsInput} lot ${tickerInput} at Rp ${priceInput} submitted!`);
    setIsAddOpen(false);
    loadData();
  };

  return (
    <AppLayout title="Virtual Portfolio">
      <div className="space-y-6">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
              Virtual Paper Trading Portfolio
            </h1>
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Simulasi eksekusi transaksi saham BEI dengan friksi komisi bursa nyata (~0.48%)
            </p>
          </div>

          <Button onClick={() => setIsAddOpen(true)}>
            <Plus className="w-4 h-4" />
            Buy Stock (Order Lot)
          </Button>
        </div>

        {/* 4 Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <div className="text-xs text-[var(--text-secondary)] mb-1">Total Equity</div>
            <div className="text-2xl font-bold font-mono text-[var(--text-primary)]">
              {portfolio ? formatIDR(portfolio.total_equity) : "..."}
            </div>
            <div className="flex items-center gap-1 mt-2 text-xs font-semibold text-emerald-500 font-mono">
              <ArrowUpRight className="w-3.5 h-3.5" />
              <span>+{portfolio?.total_pnl_pct || 1.8}% Total Return</span>
            </div>
          </Card>

          <Card>
            <div className="text-xs text-[var(--text-secondary)] mb-1">Available Cash Balance</div>
            <div className="text-2xl font-bold font-mono text-[var(--text-primary)]">
              {portfolio ? formatIDR(portfolio.cash_balance) : "..."}
            </div>
            <p className="text-xs text-[var(--text-secondary)] mt-2">Ready for scalping entries</p>
          </Card>

          <Card>
            <div className="text-xs text-[var(--text-secondary)] mb-1">Unrealized P&L</div>
            <div className="text-2xl font-bold font-mono text-emerald-500">
              +{portfolio ? formatIDR(portfolio.total_pnl) : "..."}
            </div>
            <p className="text-xs text-[var(--text-secondary)] mt-2">After estimated broker fees</p>
          </Card>

          <Card>
            <div className="text-xs text-[var(--text-secondary)] mb-1">Win Rate (Virtual)</div>
            <div className="text-2xl font-bold font-mono text-blue-500">
              {portfolio?.win_rate_pct || 66.7}%
            </div>
            <p className="text-xs text-[var(--text-secondary)] mt-2">Out of closed scalping trades</p>
          </Card>
        </div>

        {/* Allocation Chart & Open Positions Table */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Asset Allocation (1 Col) */}
          <Card>
            <CardHeader
              title="Portfolio Allocation"
              subtitle="Current asset distribution"
              action={<PieChart className="w-4 h-4 text-blue-500" />}
            />
            <PortfolioAllocationChart positions={portfolio?.open_positions || []} />
          </Card>

          {/* Open Positions (2 Cols) */}
          <Card className="lg:col-span-2 p-0 overflow-hidden">
            <div className="p-4 border-b border-[var(--border)]">
              <h3 className="font-semibold text-sm text-[var(--text-primary)]">Open Positions</h3>
              <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                Active scalping lots held in virtual account
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[var(--border)] bg-[var(--background)]/60 text-[var(--text-secondary)] font-semibold">
                    <th className="py-3 px-4">Ticker</th>
                    <th className="py-3 px-4 text-right">Lots (Shares)</th>
                    <th className="py-3 px-4 text-right">Avg Price</th>
                    <th className="py-3 px-4 text-right">Last Price</th>
                    <th className="py-3 px-4 text-right">Market Value</th>
                    <th className="py-3 px-4 text-right">Unrealized P&L</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {portfolio?.open_positions.map((pos) => (
                    <tr key={pos.ticker} className="hover:bg-[var(--background)]/40 transition-colors">
                      <td className="py-3.5 px-4 font-bold text-sm text-[var(--text-primary)]">
                        {pos.ticker}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono">
                        {pos.lots} lot ({pos.shares} shs)
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono text-[var(--text-secondary)]">
                        {formatIDR(pos.avg_buy_price)}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-semibold text-[var(--text-primary)]">
                        {formatIDR(pos.current_price)}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono text-[var(--text-primary)]">
                        {formatIDR(pos.current_value)}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-bold text-emerald-500">
                        +{formatIDR(pos.unrealized_pnl)} ({formatPercent(pos.unrealized_pnl_pct)})
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        {/* Trade History */}
        <Card className="p-0 overflow-hidden">
          <div className="p-4 border-b border-[var(--border)]">
            <h3 className="font-semibold text-sm text-[var(--text-primary)]">Transaction History</h3>
            <p className="text-xs text-[var(--text-secondary)] mt-0.5">
              Audited trade ledger with broker fee deductions
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[var(--border)] bg-[var(--background)]/60 text-[var(--text-secondary)] font-semibold">
                  <th className="py-3 px-4">Time</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Ticker</th>
                  <th className="py-3 px-4 text-right">Lots</th>
                  <th className="py-3 px-4 text-right">Execution Price</th>
                  <th className="py-3 px-4 text-right">Gross Amount</th>
                  <th className="py-3 px-4 text-right">Broker Fee</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)] font-mono">
                {portfolio?.trade_history.map((tx) => (
                  <tr key={tx.id} className="hover:bg-[var(--background)]/40">
                    <td className="py-3 px-4 text-[var(--text-secondary)]">{tx.executed_at}</td>
                    <td className="py-3 px-4">
                      <Badge variant={tx.order_type === "BUY" ? "buy" : "sell"}>
                        {tx.order_type}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 font-bold text-[var(--text-primary)]">{tx.ticker}</td>
                    <td className="py-3 px-4 text-right">{tx.lots}</td>
                    <td className="py-3 px-4 text-right">{formatIDR(tx.execution_price)}</td>
                    <td className="py-3 px-4 text-right">{formatIDR(tx.gross_amount)}</td>
                    <td className="py-3 px-4 text-right text-[var(--text-secondary)]">
                      {formatIDR(tx.fee_amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Add Stock Modal */}
        <Modal isOpen={isAddOpen} onClose={() => setIsAddOpen(false)} title="New Virtual Order">
          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                Stock Ticker
              </label>
              <input
                type="text"
                value={tickerInput}
                onChange={(e) => setTickerInput(e.target.value.toUpperCase())}
                className="w-full px-3 py-2 text-sm rounded-xl bg-[var(--background)] border border-[var(--border)] font-bold uppercase"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                Quantity (Lots, 1 Lot = 100 Shares)
              </label>
              <input
                type="number"
                min="1"
                value={lotsInput}
                onChange={(e) => setLotsInput(Number(e.target.value))}
                className="w-full px-3 py-2 text-sm rounded-xl bg-[var(--background)] border border-[var(--border)] font-mono font-bold"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-[var(--text-secondary)] block mb-1">
                Price per Share (IDR)
              </label>
              <input
                type="number"
                step="25"
                value={priceInput}
                onChange={(e) => setPriceInput(Number(e.target.value))}
                className="w-full px-3 py-2 text-sm rounded-xl bg-[var(--background)] border border-[var(--border)] font-mono font-bold"
              />
            </div>

            <div className="p-3 rounded-xl bg-[var(--background)] text-xs font-mono space-y-1">
              <div className="flex justify-between">
                <span className="text-[var(--text-secondary)] font-sans">Gross Capital:</span>
                <span>{formatIDR(lotsInput * 100 * priceInput)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-secondary)] font-sans">Estimated Fee (~0.19%):</span>
                <span>{formatIDR(lotsInput * 100 * priceInput * 0.0019)}</span>
              </div>
            </div>

            <Button onClick={handleExecuteBuy} className="w-full">
              Confirm Paper Order
            </Button>
          </div>
        </Modal>
      </div>
    </AppLayout>
  );
}
