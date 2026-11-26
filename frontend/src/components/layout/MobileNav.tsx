import React from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import {
  LayoutDashboard,
  Search,
  LineChart,
  Bot,
  Briefcase,
} from "lucide-react";
import { cn } from "../../lib/utils";

const mobileNavItems = [
  { href: "/", label: "Home", icon: LayoutDashboard },
  { href: "/screener", label: "Screener", icon: Search },
  { href: "/analysis/BBCA", label: "Analysis", icon: LineChart },
  { href: "/ai-assistant", label: "AI Copilot", icon: Bot },
  { href: "/portfolio", label: "Portfolio", icon: Briefcase },
];

export const MobileNav: React.FC = () => {
  const router = useRouter();

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-[var(--card)] border-t border-[var(--border)] px-4 flex items-center justify-around z-30 shadow-lg">
      {mobileNavItems.map((item) => {
        const Icon = item.icon;
        const isActive =
          router.pathname === item.href ||
          (item.href.startsWith("/analysis") && router.pathname.startsWith("/analysis"));

        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex flex-col items-center gap-1 py-1 px-3 rounded-lg text-[11px] font-medium transition-colors",
              isActive
                ? "text-blue-500 font-semibold"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            )}
          >
            <Icon className="w-5 h-5" />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
};
