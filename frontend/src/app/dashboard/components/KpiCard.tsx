"use client";

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";

import { AnimatedNumber } from "./AnimatedNumber";

/**
 * Glassmorphism KPI card with a glowing accent, animated value and a faint
 * radial gradient that matches the metric's tone.
 */
export function KpiCard({
  icon: Icon,
  label,
  value,
  decimals = 0,
  suffix = "",
  prefix = "",
  accent = "#22d3ee",
  hint,
  index = 0,
}: {
  icon: LucideIcon;
  label: string;
  value: number;
  decimals?: number;
  suffix?: string;
  prefix?: string;
  accent?: string;
  hint?: string;
  index?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.5, ease: "easeOut" }}
      className="group relative overflow-hidden rounded-2xl border border-zinc-800/80 bg-zinc-900/60 p-5 backdrop-blur-sm"
    >
      {/* accent glow */}
      <div
        className="pointer-events-none absolute -right-10 -top-10 h-32 w-32 rounded-full opacity-20 blur-2xl transition-opacity duration-500 group-hover:opacity-40"
        style={{ background: accent }}
      />
      <div className="relative flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
            {label}
          </p>
          <p
            className="mt-2 text-3xl font-bold tabular-nums"
            style={{ color: accent }}
          >
            <AnimatedNumber
              value={value}
              decimals={decimals}
              suffix={suffix}
              prefix={prefix}
            />
          </p>
          {hint && <p className="mt-1 text-xs text-zinc-500">{hint}</p>}
        </div>
        <div
          className="rounded-xl border border-zinc-700/60 bg-zinc-800/60 p-2.5"
          style={{ color: accent }}
        >
          <Icon size={20} strokeWidth={2} />
        </div>
      </div>
    </motion.div>
  );
}
