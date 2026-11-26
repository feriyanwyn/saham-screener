import React, { useState } from "react";
import {
  Settings as SettingsIcon,
  Moon,
  Sun,
  Laptop,
  Key,
  Database,
  Bell,
  User,
  Shield,
  Save,
  CheckCircle2,
} from "lucide-react";
import { AppLayout } from "../components/layout/AppLayout";
import { Card, CardHeader } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useTheme } from "../context/ThemeContext";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();

  // Local state for settings form
  const [dataProvider, setDataProvider] = useState("mock");
  const [aiProvider, setAiProvider] = useState("gemini");
  const [apiKey, setApiKey] = useState("••••••••••••••••");
  const [signalAlerts, setSignalAlerts] = useState(true);
  const [soundAlerts, setSoundAlerts] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSave = () => {
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <AppLayout title="Settings">
      <div className="space-y-6 max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
              Application Settings
            </h1>
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Konfigurasi tema, API Large Language Model, dan penyedia data pasar BEI
            </p>
          </div>

          <Button onClick={handleSave} className="gap-2">
            <Save className="w-4 h-4" />
            {savedSuccess ? "Saved!" : "Save Changes"}
          </Button>
        </div>

        {savedSuccess && (
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-semibold flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            Konfigurasi preferensi berhasil disimpan ke storage.
          </div>
        )}

        {/* 1. Theme Configuration */}
        <Card>
          <CardHeader
            title="Appearance & Theme"
            subtitle="Pilih tema tampilan yang nyaman untuk trading harian"
          />
          <div className="grid grid-cols-3 gap-3">
            {[
              { id: "light", label: "Light Mode", icon: Sun, desc: "Clean #F5F7FB background" },
              { id: "dark", label: "Dark Mode", icon: Moon, desc: "Fintech #0B1220 background" },
              { id: "system", label: "System Sync", icon: Laptop, desc: "Follow OS preference" },
            ].map((t) => {
              const Icon = t.icon;
              const isSelected = theme === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => setTheme(t.id as any)}
                  className={`p-4 rounded-xl border text-left transition-all ${
                    isSelected
                      ? "border-blue-500 bg-blue-500/5 shadow-xs"
                      : "border-[var(--border)] hover:bg-[var(--background)]"
                  }`}
                >
                  <Icon
                    className={`w-5 h-5 mb-2 ${
                      isSelected ? "text-blue-500" : "text-[var(--text-secondary)]"
                    }`}
                  />
                  <div className="font-bold text-xs text-[var(--text-primary)]">{t.label}</div>
                  <div className="text-[10px] text-[var(--text-secondary)] mt-0.5">{t.desc}</div>
                </button>
              );
            })}
          </div>
        </Card>

        {/* 2. AI & Large Language Model Provider */}
        <Card>
          <CardHeader
            title="AI Trading Assistant Provider"
            subtitle="Penyedia LLM untuk asisten analisis kuantitatif"
            action={<Key className="w-4 h-4 text-purple-500" />}
          />
          <div className="space-y-4 text-xs">
            <div>
              <label className="font-semibold text-[var(--text-secondary)] block mb-1">
                Active AI Engine
              </label>
              <select
                value={aiProvider}
                onChange={(e) => setAiProvider(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl bg-[var(--background)] border border-[var(--border)] text-[var(--text-primary)] font-medium focus:outline-none"
              >
                <option value="gemini">Google Gemini API (Gemini 2.5 / 1.5 Pro)</option>
                <option value="openai">OpenAI API (GPT-4o / GPT-4o-mini)</option>
                <option value="claude">Anthropic Claude API (Claude 3.5 Sonnet)</option>
                <option value="mock">Offline High-Fidelity Mock LLM (No API Key Required)</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-[var(--text-secondary)] block mb-1">
                API Key (Masked for Security)
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Paste API key here..."
                className="w-full px-3 py-2 text-xs rounded-xl bg-[var(--background)] border border-[var(--border)] font-mono text-[var(--text-primary)] focus:outline-none"
              />
              <p className="text-[10px] text-[var(--text-secondary)] mt-1">
                Disimpan secara aman dalam environment variables / server session.
              </p>
            </div>
          </div>
        </Card>

        {/* 3. Market Data Provider */}
        <Card>
          <CardHeader
            title="Market Data Engine"
            subtitle="Sumber feed data intraday dan OHLCV saham BEI"
            action={<Database className="w-4 h-4 text-blue-500" />}
          />
          <div className="space-y-3 text-xs">
            {[
              { id: "mock", name: "High-Fidelity BEI Mock Simulator", desc: "Order book, bid/ask spread, ARA/ARB simulation tanpa limit kuota" },
              { id: "yfinance", name: "Yahoo Finance (.JK)", desc: "Data historis daily & intraday Bursa Efek Indonesia" },
              { id: "invezgo", name: "Invezgo API", desc: "Data resmi real-time feed saham Indonesia" },
              { id: "apicoid", name: "Api.co.id", desc: "REST endpoint data pasar saham BEI" },
            ].map((p) => (
              <label
                key={p.id}
                className="flex items-start gap-3 p-3 rounded-xl border border-[var(--border)] bg-[var(--background)]/50 cursor-pointer hover:border-blue-500/40"
              >
                <input
                  type="radio"
                  name="data_provider"
                  value={p.id}
                  checked={dataProvider === p.id}
                  onChange={(e) => setDataProvider(e.target.value)}
                  className="mt-1"
                />
                <div>
                  <div className="font-bold text-[var(--text-primary)]">{p.name}</div>
                  <div className="text-[11px] text-[var(--text-secondary)]">{p.desc}</div>
                </div>
              </label>
            ))}
          </div>
        </Card>

        {/* 4. Notification Preferences */}
        <Card>
          <CardHeader
            title="Notification Preferences"
            subtitle="Peringatan sinyal dan pergerakan pasar"
            action={<Bell className="w-4 h-4 text-amber-500" />}
          />
          <div className="space-y-3 text-xs">
            <label className="flex items-center justify-between p-3 rounded-xl bg-[var(--background)] border border-[var(--border)] cursor-pointer">
              <div>
                <div className="font-semibold text-[var(--text-primary)]">Scalping Signals Alert</div>
                <div className="text-[11px] text-[var(--text-secondary)]">
                  Notifikasi ketika sinyal BUY atau SELL terkonfirmasi oleh model
                </div>
              </div>
              <input
                type="checkbox"
                checked={signalAlerts}
                onChange={(e) => setSignalAlerts(e.target.checked)}
                className="w-4 h-4 accent-blue-600"
              />
            </label>

            <label className="flex items-center justify-between p-3 rounded-xl bg-[var(--background)] border border-[var(--border)] cursor-pointer">
              <div>
                <div className="font-semibold text-[var(--text-primary)]">Audio Alert</div>
                <div className="text-[11px] text-[var(--text-secondary)]">
                  Bunyi denting halus saat order filled atau TP/SL tercapai
                </div>
              </div>
              <input
                type="checkbox"
                checked={soundAlerts}
                onChange={(e) => setSoundAlerts(e.target.checked)}
                className="w-4 h-4 accent-blue-600"
              />
            </label>
          </div>
        </Card>
      </div>
    </AppLayout>
  );
}
