"use client";

import { motion } from "framer-motion";
import { CalendarRange, TrendingUp, FileText } from "lucide-react";

import type { WeeklyReport } from "@/lib/api/report";

const RISK_STYLE: Record<string, { ring: string; text: string; glow: string }> = {
  높음: { ring: "border-red-500/50", text: "text-red-300", glow: "from-red-600/30" },
  보통: { ring: "border-amber-500/50", text: "text-amber-300", glow: "from-amber-600/30" },
  낮음: { ring: "border-cyan-500/50", text: "text-cyan-300", glow: "from-cyan-600/30" },
  UNKNOWN: { ring: "border-zinc-600/50", text: "text-zinc-300", glow: "from-zinc-600/30" },
};

export function WeeklyHero({ weekly }: { weekly: WeeklyReport | null }) {
  if (!weekly) {
    return (
      <div className="rounded-2xl border border-dashed border-zinc-800 p-6 text-sm text-zinc-500">
        아직 생성된 주간 리포트가 없습니다.
      </div>
    );
  }
  const risk = RISK_STYLE[weekly.risk_outlook.level] ?? RISK_STYLE.UNKNOWN;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={
        "relative overflow-hidden rounded-2xl border bg-zinc-900/60 p-6 " + risk.ring
      }
    >
      <div
        className={
          "pointer-events-none absolute -left-20 -top-20 h-64 w-64 rounded-full bg-gradient-to-br to-transparent blur-3xl " +
          risk.glow
        }
      />
      <div className="relative">
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs text-zinc-400">
            <CalendarRange size={14} /> {weekly.from} → {weekly.to}
          </span>
          <span className="flex items-center gap-1.5 rounded-full bg-zinc-800/70 px-2.5 py-0.5 text-xs text-zinc-300">
            <FileText size={12} /> {weekly.report_count} reports
          </span>
          <span
            className={
              "ml-auto flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold " +
              risk.ring +
              " " +
              risk.text
            }
          >
            <TrendingUp size={13} /> risk · {weekly.risk_outlook.level}
          </span>
        </div>

        <h2 className="mt-4 text-lg font-bold text-zinc-100">Weekly Operations Report</h2>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-zinc-300">
          {weekly.summary}
        </p>
        <p className={"mt-3 text-xs leading-relaxed " + risk.text}>
          {weekly.risk_outlook.reason}
        </p>
      </div>
    </motion.div>
  );
}
