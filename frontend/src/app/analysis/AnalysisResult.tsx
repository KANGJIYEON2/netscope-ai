"use client";

import { motion } from "framer-motion";
import { Stethoscope, Wrench, FileText, Cpu, Clock } from "lucide-react";

import { AnalysisResult as AnalysisResultType } from "@/types/analysis";
import { severityConfig, asSeverity } from "@/styles/severity";

interface AnalysisResultProps {
  result: AnalysisResultType | null;
}

export default function AnalysisResult({ result }: AnalysisResultProps) {
  if (!result) return null;

  const sev = asSeverity(result.severity);
  const cfg = severityConfig[sev];
  const pct = Math.round(result.confidence * 100);
  const sections = result.report_sections ?? [];

  return (
    <motion.article
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/40 backdrop-blur-sm"
      style={{ borderTop: `3px solid ${cfg.hex}` }}
    >
      {/* ── Report header ───────────────────────────── */}
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-zinc-800/70 p-6">
        <div className="flex items-center gap-3">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-2.5" style={{ color: cfg.hex }}>
            <FileText size={22} />
          </div>
          <div>
            <h2 className="text-lg font-bold text-zinc-100">Diagnostics Report</h2>
            <p className="mt-0.5 flex items-center gap-3 text-xs text-zinc-500">
              <span className="flex items-center gap-1">
                <Cpu size={12} /> {result.strategy_used.toUpperCase()}
              </span>
              <span className="flex items-center gap-1">
                <Clock size={12} /> {new Date(result.received_at).toLocaleString()}
              </span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <span className={cfg.badge + " rounded-full px-3 py-1 text-sm font-bold"}>
            {cfg.label}
          </span>
          <div className="text-right">
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-24 overflow-hidden rounded-full bg-zinc-800">
                <motion.div
                  className="h-full rounded-full"
                  style={{ background: cfg.hex }}
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 0.7, ease: "easeOut" }}
                />
              </div>
              <span className="text-sm font-bold tabular-nums" style={{ color: cfg.hex }}>
                {pct}%
              </span>
            </div>
            <p className="mt-0.5 text-[10px] uppercase tracking-wider text-zinc-600">
              confidence
            </p>
          </div>
        </div>
      </header>

      <div className="space-y-6 p-6">
        {/* ── Executive summary ─────────────────────── */}
        <section>
          <p
            className="rounded-xl border-l-4 bg-zinc-900/60 p-4 text-sm leading-relaxed text-zinc-100"
            style={{ borderColor: cfg.hex }}
          >
            {result.summary}
          </p>
        </section>

        {/* ── Detailed report sections (GPT) ────────── */}
        {sections.length > 0 && (
          <section className="space-y-3">
            {sections.map((s, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 + i * 0.06, duration: 0.35 }}
                className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4"
              >
                <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-zinc-100">
                  <span
                    className="flex h-5 w-5 items-center justify-center rounded-md text-[11px] font-bold"
                    style={{ background: `${cfg.hex}22`, color: cfg.hex }}
                  >
                    {i + 1}
                  </span>
                  {s.title}
                </h3>
                <p className="whitespace-pre-line text-sm leading-relaxed text-zinc-300">
                  {s.body}
                </p>
              </motion.div>
            ))}
          </section>
        )}

        {/* ── Causes / Actions ──────────────────────── */}
        <section className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-xl border border-rose-900/40 bg-rose-500/5 p-4">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-rose-300">
              <Stethoscope size={15} /> Suspected Causes
            </h3>
            <ul className="space-y-2">
              {result.suspected_causes.map((c, i) => (
                <li key={i} className="flex gap-2 text-sm leading-relaxed text-zinc-300">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-rose-400" />
                  {c}
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-xl border border-emerald-900/40 bg-emerald-500/5 p-4">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-emerald-300">
              <Wrench size={15} /> Recommended Actions
            </h3>
            <ul className="space-y-2">
              {result.recommended_actions.map((a, i) => (
                <li key={i} className="flex gap-2 text-sm leading-relaxed text-zinc-300">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                  {a}
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* ── Matched rules ─────────────────────────── */}
        {result.matched_rules.length > 0 && (
          <section>
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Matched Rules · 판단 근거
            </h3>
            <div className="flex flex-wrap gap-2">
              {result.matched_rules.map((rule, i) => (
                <span
                  key={i}
                  className="rounded-md border border-zinc-700 bg-zinc-800/60 px-2.5 py-1 font-mono text-xs text-zinc-300"
                >
                  {rule}
                </span>
              ))}
            </div>
          </section>
        )}
      </div>
    </motion.article>
  );
}
