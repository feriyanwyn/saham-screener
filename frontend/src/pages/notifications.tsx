import React, { useState } from "react";
import { Bell, ShieldAlert, CheckCircle, Clock, Trash2, CheckCheck } from "lucide-react";
import { AppLayout } from "../components/layout/AppLayout";
import { Card, CardHeader } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { NotificationAlert } from "../types";

export default function NotificationsPage() {
  const [alerts, setAlerts] = useState<NotificationAlert[]>([
    {
      id: "1",
      type: "SIGNAL",
      title: "Scalping Sinyal BUY Dikonfirmasi",
      message: "MEDC memicu sinyal BUY pada candle 5M dengan Relative Volume 2.45x dan prediksi BiLSTM probabilitas naik 74%.",
      ticker: "MEDC",
      timestamp: "5 menit lalu",
      is_read: false,
      priority: "HIGH",
    },
    {
      id: "2",
      type: "PRICE",
      title: "Target Take Profit Tercapai",
      message: "BBCA menyentuh area Take Profit Rp 10,150. Evaluasi posisi scalping Anda.",
      ticker: "BBCA",
      timestamp: "18 menit lalu",
      is_read: false,
      priority: "NORMAL",
    },
    {
      id: "3",
      type: "MODEL",
      title: "Model Deep Learning Diperbarui",
      message: "Model BiLSTM & LSTM Regressor telah menyelesaikan kalibrasi walk-forward terbaru.",
      timestamp: "1 jam lalu",
      is_read: true,
      priority: "LOW",
    },
    {
      id: "4",
      type: "WATCHLIST",
      title: "Lonjakan Volume Terdeteksi",
      message: "ADRO mengalami lonjakan transaksi > Rp 100 Miliar dalam 15 menit terakhir.",
      ticker: "ADRO",
      timestamp: "2 jam lalu",
      is_read: true,
      priority: "NORMAL",
    },
  ]);

  const markAllRead = () => {
    setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })));
  };

  const clearAlerts = () => {
    setAlerts([]);
  };

  return (
    <AppLayout title="Notifications & Alerts">
      <div className="space-y-6 max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
              Alerts & Notifications Center
            </h1>
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Pemantauan sinyal scalping, batas harga, dan pembaruan model Machine Learning
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={markAllRead}>
              <CheckCheck className="w-3.5 h-3.5" />
              Mark All Read
            </Button>
            <Button variant="outline" size="sm" onClick={clearAlerts}>
              <Trash2 className="w-3.5 h-3.5" />
              Clear
            </Button>
          </div>
        </div>

        {/* Alerts List */}
        <div className="space-y-3">
          {alerts.length === 0 ? (
            <Card className="py-12 text-center text-xs text-[var(--text-secondary)]">
              Tidak ada notifikasi aktif saat ini.
            </Card>
          ) : (
            alerts.map((alert) => (
              <Card
                key={alert.id}
                className={`p-4 transition-all ${
                  !alert.is_read
                    ? "border-blue-500/30 bg-blue-500/5 shadow-xs"
                    : "opacity-80"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div
                      className={`p-2 rounded-xl mt-0.5 ${
                        alert.type === "SIGNAL"
                          ? "bg-emerald-500/10 text-emerald-500"
                          : alert.type === "PRICE"
                          ? "bg-blue-500/10 text-blue-500"
                          : alert.type === "MODEL"
                          ? "bg-purple-500/10 text-purple-500"
                          : "bg-amber-500/10 text-amber-500"
                      }`}
                    >
                      <Bell className="w-4 h-4" />
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-[var(--text-primary)]">
                          {alert.title}
                        </span>
                        {alert.ticker && <Badge variant="primary">{alert.ticker}</Badge>}
                        {!alert.is_read && (
                          <span className="w-2 h-2 rounded-full bg-blue-500" />
                        )}
                      </div>
                      <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                        {alert.message}
                      </p>
                    </div>
                  </div>

                  <span className="text-[11px] text-[var(--text-secondary)] shrink-0 font-mono">
                    {alert.timestamp}
                  </span>
                </div>
              </Card>
            ))
          )}
        </div>
      </div>
    </AppLayout>
  );
}
