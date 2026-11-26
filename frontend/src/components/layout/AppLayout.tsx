import React, { useState } from "react";
import Head from "next/head";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { MobileNav } from "./MobileNav";
import { X, TrendingUp } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/router";

interface AppLayoutProps {
  children: React.ReactNode;
  title?: string;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children, title = "AI Stock Analyzer" }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const router = useRouter();

  return (
    <div className="min-h-screen flex flex-col bg-[var(--background)] text-[var(--text-primary)]">
      <Head>
        <title>{title} | Indonesian Stock Prediction & Scalping Assistant</title>
        <meta
          name="description"
          content="AI-powered Indonesian stock analytics, LSTM/BiLSTM deep learning price prediction, and quantitative scalping assistant for Bursa Efek Indonesia (BEI)."
        />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
      </Head>

      <div className="flex-1 flex overflow-hidden">
        {/* Desktop Sidebar */}
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />

        {/* Mobile Drawer Backdrop */}
        {mobileDrawerOpen && (
          <div
            className="md:hidden fixed inset-0 bg-black/50 z-40 backdrop-blur-xs"
            onClick={() => setMobileDrawerOpen(false)}
          />
        )}

        {/* Mobile Drawer */}
        <div
          className={`md:hidden fixed inset-y-0 left-0 w-72 bg-[var(--card)] z-50 shadow-2xl transform transition-transform duration-300 p-4 flex flex-col ${
            mobileDrawerOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <div className="flex items-center justify-between pb-4 border-b border-[var(--border)]">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white">
                <TrendingUp className="w-4 h-4" />
              </div>
              <span className="font-bold text-sm">AI Stock Analyzer</span>
            </div>
            <button
              onClick={() => setMobileDrawerOpen(false)}
              className="p-1 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--background)]"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex-1 py-4 space-y-1">
            {[
              { href: "/", label: "Dashboard" },
              { href: "/screener", label: "Stock Screener" },
              { href: "/analysis/BBCA", label: "Stock Analysis" },
              { href: "/ai-assistant", label: "AI Copilot" },
              { href: "/portfolio", label: "Portfolio" },
              { href: "/backtesting", label: "Backtesting" },
              { href: "/notifications", label: "Notifications" },
              { href: "/settings", label: "Settings" },
            ].map((m) => (
              <Link
                key={m.href}
                href={m.href}
                onClick={() => setMobileDrawerOpen(false)}
                className={`block px-3 py-2 rounded-lg text-sm font-medium ${
                  router.pathname === m.href ? "bg-blue-600 text-white" : "text-[var(--text-secondary)]"
                }`}
              >
                {m.label}
              </Link>
            ))}
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          <Header onOpenMobileMenu={() => setMobileDrawerOpen(true)} />
          <main className="flex-1 p-4 md:p-6 pb-20 md:pb-8 max-w-7xl mx-auto w-full">
            {children}
          </main>
        </div>
      </div>

      {/* Mobile Bottom Navigation */}
      <MobileNav />
    </div>
  );
};
