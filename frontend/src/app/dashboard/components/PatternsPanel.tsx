"use client";

import { motion } from "framer-motion";
import { Sparkles, ThumbsUp, ThumbsDown, Brain } from "lucide-react";

import type { LearnedPattern, PatternStatus } from "@/lib/api/patterns";

const STATUS_STYLE: Record<PatternStatus, { label: string; cls: string }> = {
  candidate: { label: "candidate", cls: "bg-zinc-700/40 text-zinc-300" },
  labeled: { label: "labeled", cls: "bg-cyan-500/20 text-cyan-300" },
  promoted: { label: "🆕 promoted", cls: "bg-emerald-500/20 text-emerald-300" },
  dismissed: { label: "dismissed", cls: "bg-zinc-800 text-zinc-500 line-through" },
};

function PatternRow({ p, index }: { p: LearnedPattern; index: number }) {
  const style = STATUS_STYLE[p.status] ?? STATUS_STYLE.candidate;
  const score = (p.score_seed ?? 0) + (p.score_adjust ?? 0);
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.4 }}
      className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3"
    >
      <div className="flex items-center justify-between gap-2">
        <span className={"rounded-full px-2 py-0.5 text-[10px] font-semibold " + style.cls}>
          {style.label}
        </span>
        <div className="flex items-center gap-3 text-[11px] text-zinc-500">
          <span className="flex items-center gap-1 text-emerald-400">
            <ThumbsUp size={11} /> {p.confirm_count}
          </span>
          <span className="flex items-center gap-1 text-rose-400">
            <ThumbsDown size={11} /> {p.dismiss_count}
          </span>
          <span className="tabular-nums">×{p.total_count}</span>
        </div>
      </div>
      <p className="mt-2 truncate font-mono text-xs text-zinc-300" title={p.template}>
        {p.display_name || p.template}
      </p>
      <div className="mt-2 flex items-center gap-2">
        <div className="h-1 flex-1 overflow-hidden rounded-full bg-zinc-800">
          <div
            className="h-full rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-400"
            style={{ width: `${Math.min(100, Math.max(0, score * 100))}%` }}
          />
        </div>
        <span className="text-[10px] tabular-nums text-zinc-500">
          {score.toFixed(2)}
        </span>
      </div>
    </motion.div>
  );
}

export function PatternsPanel({ patterns }: { patterns: LearnedPattern[] }) {
  return (
    <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/40 p-5 backdrop-blur-sm">
      <div className="mb-4 flex items-center gap-2">
        <Brain size={16} className="text-violet-400" />
        <h3 className="text-sm font-semibold text-zinc-200">Learned Patterns</h3>
        <span className="ml-auto rounded-full bg-violet-500/15 px-2 py-0.5 text-[10px] font-medium text-violet-300">
          L0–L4
        </span>
      </div>
      {patterns.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-10 text-center">
          <Sparkles size={26} className="text-zinc-600" />
          <p className="text-xs text-zinc-500">
            아직 학습된 패턴이 없습니다.
            <br />
            로그가 수집되면 Drain 마이닝이 패턴을 발견합니다.
          </p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {patterns.map((p, i) => (
            <PatternRow key={p.id} p={p} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}
