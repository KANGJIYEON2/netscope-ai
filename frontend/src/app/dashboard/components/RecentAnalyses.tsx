"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Stethoscope, Wrench, ChevronDown, Cpu } from "lucide-react";

import type { ReportSummary } from "@/lib/api/report";
import { severityConfig, asSeverity } from "@/styles/severity";

function ConfidenceBar({ value, hex }: { value: number; hex: string }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-zinc-800">
        <motion.div
          className="h-full rounded-full"
          style={{ background: hex }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.7, ease: "easeOut" }}
        />
      </div>
      <span className="text-xs font-semibold tabular-nums" style={{ color: hex }}>
        {pct}%
      </span>
    </div>
  );
}

function AnalysisRow({ r, index }: { r: ReportSummary; index: number }) {
  const [open, setOpen] = useState(false);
  const sev = asSeverity(r.severity);
  const cfg = severityConfig[sev];
  const hasDetail =
    (r.suspected_causes?.length ?? 0) > 0 ||
    (r.recommended_actions?.length ?? 0) > 0;

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05, duration: 0.4 }}
      className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/50"
      style={{ borderLeft: `4px solid ${cfg.hex}` }}
    >
      <button
        onClick={() => hasDetail && setOpen((o) => !o)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left"
      >
        <span className={cfg.badge + " rounded-full px-2.5 py-0.5 text-xs font-semibold"}>
          {cfg.label}
        </span>
        <p className="min-w-0 flex-1 truncate text-sm text-zinc-200">
          {r.summary}
        </p>
        <ConfidenceBar value={r.confidence} hex={cfg.hex} />
        <span className="hidden items-center gap-1 rounded-md bg-zinc-800 px-2 py-0.5 text-[10px] font-medium uppercase text-zinc-400 sm:flex">
          <Cpu size={11} /> {r.strategy_used}
        </span>
        <span className="hidden text-xs text-zinc-500 md:block">
          {new Date(r.received_at).toLocaleString()}
        </span>
        {hasDetail && (
          <ChevronDown
            size={16}
            className={
              "shrink-0 text-zinc-500 transition-transform " +
              (open ? "rotate-180" : "")
            }
          />
        )}
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="border-t border-zinc-800/70"
          >
            <div className="grid gap-4 px-4 py-4 sm:grid-cols-2">
              <div>
                <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-rose-300">
                  <Stethoscope size={13} /> Suspected causes
                </p>
                <ul className="space-y-1">
                  {(r.suspected_causes ?? []).map((c, i) => (
                    <li key={i} className="text-xs leading-relaxed text-zinc-400">
                      • {c}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-emerald-300">
                  <Wrench size={13} /> Recommended actions
                </p>
                <ul className="space-y-1">
                  {(r.recommended_actions ?? []).map((a, i) => (
                    <li key={i} className="text-xs leading-relaxed text-zinc-400">
                      • {a}
                    </li>
                  ))}
                </ul>
              </div>
              {r.matched_rules?.length > 0 && (
                <div className="sm:col-span-2">
                  <div className="flex flex-wrap gap-1.5">
                    {r.matched_rules.map((rule) => (
                      <span
                        key={rule}
                        className="rounded-md border border-zinc-700 bg-zinc-800/70 px-2 py-0.5 font-mono text-[10px] text-zinc-300"
                      >
                        {rule}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function RecentAnalyses({ reports }: { reports: ReportSummary[] }) {
  if (reports.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-zinc-800 py-12 text-center">
        <Cpu size={28} className="text-zinc-600" />
        <p className="text-sm text-zinc-500">아직 분석 결과가 없습니다.</p>
      </div>
    );
  }
  return (
    <div className="space-y-2.5">
      {reports.map((r, i) => (
        <AnalysisRow key={i} r={r} index={i} />
      ))}
    </div>
  );
}
