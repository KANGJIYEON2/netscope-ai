"use client";

import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Brain,
  ThumbsUp,
  ThumbsDown,
  XCircle,
  Tag,
  Sparkles,
} from "lucide-react";

import {
  fetchPatterns,
  labelPattern,
  dismissPattern,
  sendPatternFeedback,
  type LearnedPattern,
  type PatternStatus,
} from "@/lib/api/patterns";
import { Card } from "@/app/components/ui/Card";

const STATUS_TABS: (PatternStatus | "all")[] = [
  "all",
  "candidate",
  "labeled",
  "promoted",
  "dismissed",
];

const STATUS_STYLE: Record<PatternStatus, string> = {
  candidate: "bg-zinc-700/40 text-zinc-300",
  labeled: "bg-cyan-500/20 text-cyan-300",
  promoted: "bg-emerald-500/20 text-emerald-300",
  dismissed: "bg-zinc-800 text-zinc-500 line-through",
};

function LabelForm({
  pattern,
  onDone,
}: {
  pattern: LearnedPattern;
  onDone: () => void;
}) {
  const [label, setLabel] = useState(pattern.label ?? "");
  const [displayName, setDisplayName] = useState(pattern.display_name ?? "");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!label.trim()) return;
    setBusy(true);
    try {
      await labelPattern(pattern.id, {
        label: label.trim(),
        display_name: displayName.trim() || undefined,
      });
      onDone();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
      <input
        value={label}
        onChange={(e) => setLabel(e.target.value)}
        placeholder="label (예: db_timeout)"
        className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-1.5 text-xs outline-none focus:border-cyan-600"
      />
      <input
        value={displayName}
        onChange={(e) => setDisplayName(e.target.value)}
        placeholder="display name (선택)"
        className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-1.5 text-xs outline-none focus:border-cyan-600"
      />
      <button
        onClick={submit}
        disabled={busy}
        className="rounded-lg bg-cyan-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-cyan-500 disabled:opacity-50"
      >
        저장
      </button>
    </div>
  );
}

function PatternCard({
  p,
  index,
  onChanged,
}: {
  p: LearnedPattern;
  index: number;
  onChanged: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const score = (p.score_seed ?? 0) + (p.score_adjust ?? 0);

  const act = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    try {
      await fn();
      onChanged();
    } finally {
      setBusy(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.35 }}
      className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4"
    >
      <div className="flex items-center justify-between gap-2">
        <span className={"rounded-full px-2 py-0.5 text-[10px] font-semibold " + STATUS_STYLE[p.status]}>
          {p.status === "promoted" ? "🆕 promoted" : p.status}
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

      <p className="mt-2 break-all font-mono text-xs text-zinc-300">
        {p.display_name || p.template}
      </p>
      {p.sources && p.sources.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {p.sources.slice(0, 6).map((s) => (
            <span key={s} className="rounded bg-zinc-800/70 px-1.5 py-0.5 text-[10px] text-zinc-400">
              {s}
            </span>
          ))}
        </div>
      )}

      <div className="mt-3 flex items-center gap-2">
        <div className="h-1 flex-1 overflow-hidden rounded-full bg-zinc-800">
          <div
            className="h-full rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-400"
            style={{ width: `${Math.min(100, Math.max(0, score * 100))}%` }}
          />
        </div>
        <span className="text-[10px] tabular-nums text-zinc-500">score {score.toFixed(2)}</span>
      </div>

      {/* Actions */}
      <div className="mt-3 flex flex-wrap items-center gap-1.5">
        <button
          disabled={busy}
          onClick={() => act(() => sendPatternFeedback(p.id, "confirm"))}
          className="flex items-center gap-1 rounded-md border border-emerald-700/50 bg-emerald-500/10 px-2 py-1 text-[11px] text-emerald-300 hover:bg-emerald-500/20 disabled:opacity-50"
        >
          <ThumbsUp size={12} /> confirm
        </button>
        <button
          disabled={busy}
          onClick={() => act(() => sendPatternFeedback(p.id, "wrong"))}
          className="flex items-center gap-1 rounded-md border border-amber-700/50 bg-amber-500/10 px-2 py-1 text-[11px] text-amber-300 hover:bg-amber-500/20 disabled:opacity-50"
        >
          <XCircle size={12} /> wrong
        </button>
        <button
          disabled={busy}
          onClick={() => act(() => dismissPattern(p.id))}
          className="flex items-center gap-1 rounded-md border border-zinc-700 bg-zinc-800/60 px-2 py-1 text-[11px] text-zinc-400 hover:bg-zinc-700/60 disabled:opacity-50"
        >
          <ThumbsDown size={12} /> dismiss
        </button>
        <button
          onClick={() => setEditing((e) => !e)}
          className="flex items-center gap-1 rounded-md border border-cyan-700/50 bg-cyan-500/10 px-2 py-1 text-[11px] text-cyan-300 hover:bg-cyan-500/20"
        >
          <Tag size={12} /> label
        </button>
      </div>

      <AnimatePresence>
        {editing && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
          >
            <LabelForm
              pattern={p}
              onDone={() => {
                setEditing(false);
                onChanged();
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function ProjectPatternsTab() {
  const [patterns, setPatterns] = useState<LearnedPattern[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<PatternStatus | "all">("all");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchPatterns({
        limit: 100,
        status: tab === "all" ? undefined : tab,
      }).catch(() => ({ total: 0, items: [] }));
      setPatterns(res.items);
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Brain size={18} className="text-violet-400" />
        <h2 className="text-sm font-semibold text-zinc-200">
          Learned Patterns
        </h2>
        <span className="rounded-full bg-violet-500/15 px-2 py-0.5 text-[10px] font-medium text-violet-300">
          L0–L4 · tenant 공유
        </span>
        <div className="ml-auto flex items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900/60 p-1">
          {STATUS_TABS.map((s) => (
            <button
              key={s}
              onClick={() => setTab(s)}
              className={
                "rounded-md px-2.5 py-1 text-xs font-medium capitalize transition-colors " +
                (tab === s ? "bg-zinc-700 text-white" : "text-zinc-400 hover:text-zinc-100")
              }
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-40 animate-pulse rounded-xl bg-zinc-800/40" />
          ))}
        </div>
      ) : patterns.length === 0 ? (
        <Card>
          <div className="flex flex-col items-center gap-2 py-14 text-center">
            <Sparkles size={28} className="text-zinc-600" />
            <p className="text-sm text-zinc-500">
              해당 상태의 학습 패턴이 없습니다.
              <br />
              로그가 수집되면 Drain 마이닝이 패턴을 발견합니다.
            </p>
          </div>
        </Card>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {patterns.map((p, i) => (
            <PatternCard key={p.id} p={p} index={i} onChanged={load} />
          ))}
        </div>
      )}
    </div>
  );
}
