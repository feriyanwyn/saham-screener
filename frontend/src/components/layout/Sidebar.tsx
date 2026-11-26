import React from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import {
  LayoutDashboard,
  Search,
  LineChart,
  Bot,
  Briefcase,
  History,
  Bell,
  Settings,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  ShieldAlert,
} from "lucide-react";
import { cn } from "../../lib/utils";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/screener", label: "Stock Screener", icon: Search, badge: "Live" },
  { href: "/analysis/BBCA", label: "Stock Analysis", icon: LineChart },
  { href: "/ai-assistant", label: "AI Copilot", icon: Bot, badge: "AI" },
  { href: "/portfolio", label: "Portfolio", icon: Briefcase },
  { href: "/backtesting", label: "Backtesting", icon: History },
  { href: "/notifications", label: "Notifications", icon: Bell },
  { href: "/settings", label: "Settings", icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const router = useRouter();

  return (
    <aside
      className={cn(
        "hidden md:flex flex-col border-r border-[var(--border)] bg-[var(--card)] transition-all duration-300 relative z-30 select-none",
        collapsed ? "w-[76px]" : "w-[260px]"
      )}
    >
      {/* Brand Header */}
      <div className="h-[68px] flex items-center justify-between px-4 border-b border-[var(--border)]">
        <Link href="/" className="flex items-center gap-3 overflow-hidden">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-blue-500/20 shrink-0">
            <TrendingUp className="w-5 h-5" />
          </div>
          {!collapsed && (
            <div className="flex flex-col min-w-0">
              <span className="font-bold text-[15px] leading-tight tracking-tight text-[var(--text-primary)] truncate">
                AI Stock Analyzer
              </span>
              <span className="text-[11px] text-[var(--text-secondary)] font-medium">
                IDX Scalping Assistant
              </span>
            </div>
          )}
        </Link>
        <button
          onClick={onToggle}
          className="p-1.5 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--background)] transition-colors"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 py-4 px-3 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            router.pathname === item.href ||
            (item.href.startsWith("/analysis") && router.pathname.startsWith("/analysis"));

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group relative",
                isActive
                  ? "bg-blue-600 text-white shadow-sm shadow-blue-500/25 font-semibold"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--background)]"
              )}
            >
              <Icon className={cn("w-5 h-5 shrink-0 transition-transform group-hover:scale-105", isActive ? "text-white" : "text-[var(--text-secondary)]")} />
              {!collapsed && <span className="truncate flex-1">{item.label}</span>}
              {!collapsed && item.badge && (
                <span
                  className={cn(
                    "text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider",
                    isActive ? "bg-white/20 text-white" : "bg-blue-500/10 text-blue-500"
                  )}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer Info Box */}
      {!collapsed && (
        <div className="p-4 m-3 rounded-xl border border-[var(--border)] bg-[var(--background)]/60 text-xs text-[var(--text-secondary)]">
          <div className="flex items-center gap-2 mb-1.5 text-[var(--text-primary)] font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-live" />
            <span>BEI Market Active</span>
          </div>
          <p className="text-[11px] leading-relaxed">
            Scalping rules & fees (~0.48%) active. Decision support system.
          </p>
        </div>
      )}
    </aside>
  );
};
