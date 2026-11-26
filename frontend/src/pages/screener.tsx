import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Search,
  Filter,
  Download,
  ArrowUpDown,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { AppLayout } from "../components/layout/AppLayout";
import { Card, CardHeader } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { apiService } from "../services/api";
import { ScreenerResult, SignalType } from "../types";
import { formatIDR, formatNumber, formatPercent } from "../lib/utils";

const SECTORS = [
  "ALL",
  "Energy",
  "Basic Materials",
  "Industrials",
  "Consumer Non-Cyclicals",
  "Consumer Cyclicals",
  "Healthcare",
  "Financials",
  "Properties & Real Estate",
  "Technology",
  "Infrastructures",
  "Transportation & Logistic",
];

export default function ScreenerPage() {
  const [stocks, setStocks] = useState<ScreenerResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedSector, setSelectedSector] = useState("ALL");
  const [signalFilter, setSignalFilter] = useState<string>("ALL");
  const [minRelVol, setMinRelVol] = useState(1.0);
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const loadData = async () => {
    setLoading(true);
    try {
      const results = await apiService.runScreener({ minRelVol });
      setStocks(results);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [minRelVol]);

  const filteredStocks = stocks.filter((s) => {
    const matchSearch =
      s.ticker.toLowerCase().includes(search.toLowerCase()) ||
      s.name.toLowerCase().includes(search.toLowerCase());
    const matchSector = selectedSector === "ALL" || s.sector === selectedSector;
    const matchSignal = signalFilter === "ALL" || s.signal === signalFilter;
    return matchSearch && matchSector && matchSignal;
  });

  const totalPages = Math.ceil(filteredStocks.length / pageSize) || 1;
  const pagedStocks = filteredStocks.slice((page - 1) * pageSize, page * pageSize);

  const exportCSV = () => {
    const headers = "Ticker,Name,Sector,Price,ChangePct,Volume,RelVol,RSI,Signal,Score\n";
    const rows = filteredStocks
      .map(
        (s) =>
          `"${s.ticker}","${s.name}","${s.sector}",${s.last_price},${s.change_pct},${s.volume},${s.relative_volume},${s.rsi_14},"${s.signal}",${s.scalping_score}`
      )
      .join("\n");
    const blob = new Blob([headers + rows], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `idx_screener_results_${Date.now()}.csv`);
    link.click();
  };

  return (
    <AppLayout title="Stock Screener">
      <div className="space-y-6">
        {/* Page Title & Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
              Multi-Factor Stock Screener
            </h1>
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Screening seluruh universe BEI berdasarkan Likuiditas, Relative Volume, RSI, dan Momentum
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={exportCSV}>
              <Download className="w-3.5 h-3.5" />
              Export CSV
            </Button>
            <Button size="sm" onClick={loadData} disabled={loading}>
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              Scan Market
            </Button>
          </div>
        </div>

        {/* Filters Toolbar */}
        <Card className="p-4 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 text-[var(--text-secondary)] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search ticker or name..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-[var(--background)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>

            {/* Sector Dropdown */}
            <div>
              <select
                value={selectedSector}
                onChange={(e) => setSelectedSector(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl bg-[var(--background)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              >
                {SECTORS.map((sec) => (
                  <option key={sec} value={sec}>
                    Sektor: {sec}
                  </option>
                ))}
              </select>
            </div>

            {/* Signal Filter */}
            <div>
              <select
                value={signalFilter}
                onChange={(e) => setSignalFilter(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl bg-[var(--background)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              >
                <option value="ALL">Semua Sinyal (BUY/SELL/HOLD)</option>
                <option value="BUY">BUY Only</option>
                <option value="SELL">SELL Only</option>
                <option value="HOLD">HOLD Only</option>
              </select>
            </div>

            {/* Min Relative Volume */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[var(--background)] border border-[var(--border)] text-xs">
              <span className="text-[var(--text-secondary)] whitespace-nowrap">RelVol ≥</span>
              <input
                type="number"
                step="0.2"
                min="0.5"
                max="5.0"
                value={minRelVol}
                onChange={(e) => setMinRelVol(Number(e.target.value))}
                className="w-16 bg-transparent font-bold text-[var(--text-primary)] text-center focus:outline-none font-mono"
              />
              <span className="text-[var(--text-secondary)]">x</span>
            </div>
          </div>
        </Card>

        {/* Screener Table */}
        <Card className="p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[var(--border)] bg-[var(--background)]/60 text-[var(--text-secondary)] font-semibold">
                  <th className="py-3 px-4">Ticker</th>
                  <th className="py-3 px-4">Company & Sector</th>
                  <th className="py-3 px-4 text-right">Last Price</th>
                  <th className="py-3 px-4 text-right">Change %</th>
                  <th className="py-3 px-4 text-right">Rel Volume</th>
                  <th className="py-3 px-4 text-right">RSI 14</th>
                  <th className="py-3 px-4 text-center">Scalping Signal</th>
                  <th className="py-3 px-4 text-right">Score</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {pagedStocks.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-12 text-center text-[var(--text-secondary)]">
                      Tidak ada saham yang memenuhi kriteria filter saat ini.
                    </td>
                  </tr>
                ) : (
                  pagedStocks.map((s) => (
                    <tr
                      key={s.ticker}
                      className="hover:bg-[var(--background)]/40 transition-colors"
                    >
                      <td className="py-3.5 px-4 font-bold text-sm text-[var(--text-primary)]">
                        <Link href={`/analysis/${s.ticker}`} className="hover:text-blue-500">
                          {s.ticker}
                        </Link>
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="text-[var(--text-primary)] font-medium truncate max-w-[200px]">
                          {s.name}
                        </div>
                        <div className="text-[10px] text-[var(--text-secondary)]">{s.sector}</div>
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-semibold text-[var(--text-primary)]">
                        {formatIDR(s.last_price)}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-bold">
                        <span className={s.change_pct >= 0 ? "text-emerald-500" : "text-rose-500"}>
                          {formatPercent(s.change_pct)}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono text-[var(--text-primary)]">
                        <span
                          className={`font-semibold ${
                            s.relative_volume >= 1.5 ? "text-blue-500 font-bold" : ""
                          }`}
                        >
                          {s.relative_volume.toFixed(2)}x
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono text-[var(--text-primary)]">
                        <span
                          className={
                            s.rsi_14 >= 70
                              ? "text-rose-500 font-bold"
                              : s.rsi_14 <= 30
                              ? "text-emerald-500 font-bold"
                              : ""
                          }
                        >
                          {s.rsi_14.toFixed(1)}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <Badge
                          variant={
                            s.signal === "BUY"
                              ? "buy"
                              : s.signal === "SELL"
                              ? "sell"
                              : s.signal === "HOLD"
                              ? "hold"
                              : "neutral"
                          }
                        >
                          {s.signal}
                        </Badge>
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-bold text-blue-500">
                        {s.scalping_score}/100
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <Link href={`/analysis/${s.ticker}`}>
                          <Button size="sm" variant="outline">
                            Analyze
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--border)] text-xs text-[var(--text-secondary)]">
            <span>
              Showing {filteredStocks.length > 0 ? (page - 1) * pageSize + 1 : 0} to{" "}
              {Math.min(page * pageSize, filteredStocks.length)} of {filteredStocks.length} emiten
            </span>
            <div className="flex items-center gap-1">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                Previous
              </Button>
              <span className="px-3 font-semibold text-[var(--text-primary)]">
                Page {page} of {totalPages}
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
              >
                Next
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </AppLayout>
  );
}
