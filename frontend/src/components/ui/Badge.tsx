import React from "react";
import { cn } from "../../lib/utils";

export type BadgeVariant = "buy" | "sell" | "hold" | "neutral" | "primary" | "demo";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = "neutral", className }) => {
  const variantStyles = {
    buy: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
    sell: "bg-rose-500/10 text-rose-500 border-rose-500/20",
    hold: "bg-amber-500/10 text-amber-500 border-amber-500/20",
    neutral: "bg-slate-500/10 text-slate-500 border-slate-500/20",
    primary: "bg-blue-500/10 text-blue-500 border-blue-500/20",
    demo: "bg-purple-500/10 text-purple-400 border-purple-500/20 font-bold tracking-wider",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border",
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  );
};
