import React, { useState } from "react";
import { AppLayout } from "../components/layout/AppLayout";
import { AIAssistantChat } from "../components/ai/AIAssistantChat";
import { Card, CardHeader } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Sparkles, Bot, BrainCircuit, ShieldAlert, TrendingUp, Scale } from "lucide-react";

export default function AIAssistantPage() {
  const [selectedTopic, setSelectedTopic] = useState("scalping");

  return (
    <AppLayout title="AI Assistant">
      <div className="space-y-6">
        {/* Header Banner */}
        <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-700 text-white shadow-lg shadow-blue-500/10">
          <div className="max-w-2xl space-y-2">
            <div className="flex items-center gap-2">
              <span className="p-1 rounded-lg bg-white/20">
                <Bot className="w-5 h-5 text-white" />
              </span>
              <span className="font-bold text-sm tracking-wider uppercase text-blue-100">
                AI Quantitative Copilot
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              AI Decision Support & Scalping Intelligence
            </h1>
            <p className="text-xs sm:text-sm text-blue-100 leading-relaxed">
              Didukung oleh model Deep Learning (LSTM & BiLSTM) dan Rule-Based Validator yang mematuhi fraksi harga resmi BEI, batas ARA/ARB, serta friksi komisi bursa.
            </p>
          </div>
        </div>

        {/* 2 Columns: Multi-Stock Ranking / Quick Insight & Full AI Chat */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: AI Multi-Stock Ranking & Guardrails (1 Col) */}
          <div className="space-y-6">
            <Card>
              <CardHeader
                title="AI Stock Ranking"
                subtitle="Best momentum & scalping quality"
                action={<Sparkles className="w-4 h-4 text-blue-500" />}
              />
              <div className="space-y-3">
                {[
                  { ticker: "MEDC", name: "Medco Energi", score: 92, badge: "STRONG_BUY", reason: "Lonjakan volume komoditas + breakout EMA 20" },
                  { ticker: "BBCA", name: "Bank Central Asia", score: 88, badge: "BUY", reason: "Inflow institusi konsisten di atas VWAP" },
                  { ticker: "BRIS", name: "Bank Syariah Ind", score: 82, badge: "BUY", reason: "BiLSTM probabilitas naik 74%" },
                  { ticker: "TLKM", name: "Telkom Indonesia", score: 55, badge: "HOLD", reason: "Konsolidasi sempit dekat garis resisten" },
                  { ticker: "GOTO", name: "GoTo Gojek Toko", score: 28, badge: "AVOID", reason: "Tekanan jual tinggi pada level bid" },
                ].map((item) => (
                  <div
                    key={item.ticker}
                    className="p-3 rounded-xl bg-[var(--background)] border border-[var(--border)] space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-[var(--text-primary)]">{item.ticker}</span>
                      <Badge
                        variant={
                          item.badge.includes("BUY")
                            ? "buy"
                            : item.badge === "HOLD"
                            ? "hold"
                            : "sell"
                        }
                      >
                        {item.badge}
                      </Badge>
                    </div>
                    <p className="text-[11px] text-[var(--text-secondary)]">{item.reason}</p>
                    <div className="flex items-center justify-between pt-1 text-[10px] font-mono">
                      <span className="text-[var(--text-secondary)]">Score:</span>
                      <span className="text-blue-500 font-bold">{item.score}/100</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="bg-[var(--card)] border-amber-500/20 space-y-2">
              <div className="flex items-center gap-2 text-amber-500 font-bold text-xs">
                <ShieldAlert className="w-4 h-4" />
                <span>Quantitative Gatekeeper Rules</span>
              </div>
              <ul className="text-xs text-[var(--text-secondary)] space-y-1.5 list-disc pl-4 leading-relaxed">
                <li>Menolak sinyal jika jarak ke batas ARA &lt; 2 tick.</li>
                <li>Mengharuskan rasio Risk/Reward bersih &ge; 1.5x setelah potongan komisi ~0.48%.</li>
                <li>Level Stop Loss &amp; Take Profit dibulatkan tepat ke fraksi harga resmi BEI.</li>
              </ul>
            </Card>
          </div>

          {/* Right Column: Interactive Copilot Chat (2 Cols) */}
          <div className="lg:col-span-2">
            <AIAssistantChat initialTicker="BBCA" className="h-full min-h-[580px]" />
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
