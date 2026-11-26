import React, { useState } from "react";
import { useRouter } from "next/router";
import {
  Sun,
  Moon,
  Laptop,
  Search,
  Bell,
  Activity,
  Menu,
} from "lucide-react";
import { useTheme } from "../../context/ThemeContext";
import { cn } from "../../lib/utils";

interface HeaderProps {
  onOpenMobileMenu?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenMobileMenu }) => {
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const [searchTicker, setSearchTicker] = useState("");

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchTicker.trim()) {
      router.push(`/analysis/${searchTicker.trim().toUpperCase()}`);
      setSearchTicker("");
    }
  };

  return (
    <header className="h-[68px] border-b border-[var(--border)] bg-[var(--card)] px-4 md:px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Left: Mobile hamburger & Global Search */}
      <div className="flex items-center gap-3 flex-1 max-w-md">
        <button
          onClick={onOpenMobileMenu}
          className="md:hidden p-2 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--background)]"
          aria-label="Open navigation drawer"
        >
          <Menu className="w-5 h-5" />
        </button>

        <form onSubmit={handleSearchSubmit} className="relative w-full">
          <Search className="w-4 h-4 text-[var(--text-secondary)] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search ticker (e.g. BBCA, MEDC, TLKM)..."
            value={searchTicker}
            onChange={(e) => setSearchTicker(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm rounded-xl bg-[var(--background)] border border-[var(--border)] text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all uppercase"
          />
        </form>
      </div>

      {/* Right: IHSG Pill, Theme Switcher, Notifications, Profile */}
      <div className="flex items-center gap-2 md:gap-4">
        {/* IHSG Ticker Pill */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--background)] border border-[var(--border)] text-xs font-medium">
          <Activity className="w-3.5 h-3.5 text-blue-500 animate-pulse" />
          <span className="text-[var(--text-secondary)]">IHSG</span>
          <span className="font-semibold text-[var(--text-primary)] font-tabular">7,285.50</span>
          <span className="text-emerald-500 font-semibold font-tabular">+0.45%</span>
        </div>

        {/* Theme Switcher Segmented Control */}
        <div className="flex items-center p-1 rounded-xl bg-[var(--background)] border border-[var(--border)] text-xs">
          <button
            onClick={() => setTheme("light")}
            className={cn(
              "p-1.5 rounded-lg transition-colors",
              theme === "light"
                ? "bg-[var(--card)] text-blue-500 shadow-sm"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            )}
            title="Light Mode"
          >
            <Sun className="w-4 h-4" />
          </button>
          <button
            onClick={() => setTheme("dark")}
            className={cn(
              "p-1.5 rounded-lg transition-colors",
              theme === "dark"
                ? "bg-[var(--card)] text-blue-400 shadow-sm"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            )}
            title="Dark Mode"
          >
            <Moon className="w-4 h-4" />
          </button>
          <button
            onClick={() => setTheme("system")}
            className={cn(
              "p-1.5 rounded-lg transition-colors",
              theme === "system"
                ? "bg-[var(--card)] text-blue-500 shadow-sm"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            )}
            title="System Preference"
          >
            <Laptop className="w-4 h-4" />
          </button>
        </div>

        {/* Notifications Icon Button */}
        <button
          onClick={() => router.push("/notifications")}
          className="relative p-2 rounded-xl text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--background)] transition-colors"
          title="Alerts and notifications"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-blue-500" />
        </button>

        {/* User Chip */}
        <div className="flex items-center gap-2 pl-2 border-l border-[var(--border)]">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shadow-sm">
            TR
          </div>
          <div className="hidden lg:flex flex-col text-left">
            <span className="text-xs font-semibold text-[var(--text-primary)] leading-none">Trader Pro</span>
            <span className="text-[10px] text-[var(--text-secondary)] leading-tight mt-0.5">Scalping Mode</span>
          </div>
        </div>
      </div>
    </header>
  );
};
