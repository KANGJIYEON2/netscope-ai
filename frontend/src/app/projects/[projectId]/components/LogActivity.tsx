"use client";

import { motion } from "framer-motion";
import { ScrollText } from "lucide-react";

import type { LogItem } from "@/types/log";
import { timeAgo } from "@/lib/time";

const LEVELS = ["ERROR", "WARN", "INFO", "DEBUG"] as const;
const LEVEL_HEX: Record<string, string> = {
  ERROR: "#f87171",
  WARN: "#fbbf24",
  INFO: "#22d3ee",
  DEBUG: "#71717a",
};

/**
 * Project-scoped log activity: level distribution bar + recent log stream.
 * This is what makes the per-project Overview log-centric (vs the fleet view).
 */
export function LogActivity({ logs }: { logs: LogItem[] }) {
  const total = logs.length || 1;
  const counts = LEVELS.map((lv) => ({
    lv,
    n: logs.filter((l) => l.level === lv).length,
  }));
  const recent = [...logs]
    .sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )
    .slice(0, 10);

  return (
    <div className="space-y-4">
      {/* distribution bar */}
      <div>
        <div className="flex h-3 overflow-hidden rounded-full bg-zinc-800">
          {counts.map(({ lv, n }) =>
            n > 0 ? (
              <motion.div
                key={lv}
                initial={{ width: 0 }}
                animate={{ width: `${(n / total) * 100}%` }}
                transition={{ duration: 0.6, ease: "easeOut" }}
                style={{ background: LEVEL_HEX[lv] }}
                title={`${lv} ${n}`}
              />
            ) : null
          )}
        </div>
        <div className="mt-2 flex flex-wrap gap-3">
          {counts.map(({ lv, n }) => (
            <span key={lv} className="flex items-center gap-1.5 text-xs text-zinc-400">
              <span className="h-2.5 w-2.5 rounded-sm" style={{ background: LEVEL_HEX[lv] }} />
              {lv} <b className="tabular-nums text-zinc-200">{n}</b>
            </span>
          ))}
        </div>
      </div>

      {/* recent stream */}
      {recent.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-8 text-center">
          <ScrollText size={26} className="text-zinc-600" />
          <p className="text-sm text-zinc-500">수집된 로그가 없습니다.</p>
        </div>
      ) : (
        <div className="space-y-1">
          {recent.map((l, i) => (
            <motion.div
              key={l.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.03, duration: 0.3 }}
              className="flex items-center gap-3 rounded-lg px-2 py-1.5 hover:bg-zinc-800/40"
            >
              <span
                className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold"
                style={{
                  background: `${LEVEL_HEX[l.level] ?? LEVEL_HEX.DEBUG}22`,
                  color: LEVEL_HEX[l.level] ?? LEVEL_HEX.DEBUG,
                }}
              >
                {l.level}
              </span>
              <span className="shrink-0 font-mono text-[11px] text-zinc-500">{l.source}</span>
              <span className="min-w-0 flex-1 truncate text-xs text-zinc-300" title={l.message}>
                {l.message}
              </span>
              <span className="shrink-0 text-[10px] text-zinc-600">{timeAgo(l.timestamp)}</span>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
