"use client";

import { motion } from "framer-motion";

import { ruleIdOf } from "@/lib/time";
import type { FleetIssue } from "./useFleetData";

type RuleAgg = {
  ruleId: string;
  label: string;
  count: number;
  projects: Set<string>;
};

/** Recurring issues across the fleet, grouped by rule id. */
export function TopIssues({ issues }: { issues: FleetIssue[] }) {
  const map = new Map<string, RuleAgg>();
  for (const issue of issues) {
    for (const rule of issue.matched_rules ?? []) {
      const id = ruleIdOf(rule);
      const cur =
        map.get(id) ??
        { ruleId: id, label: rule, count: 0, projects: new Set<string>() };
      cur.count += 1;
      cur.projects.add(issue.projectId);
      map.set(id, cur);
    }
  }

  const top = [...map.values()].sort((a, b) => b.count - a.count).slice(0, 8);
  const max = Math.max(1, ...top.map((t) => t.count));

  if (top.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-zinc-500">
        재발 이슈가 없습니다.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {top.map((t, i) => (
        <motion.div
          key={t.ruleId}
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.05, duration: 0.35 }}
        >
          <div className="flex items-center justify-between text-xs">
            <span className="flex items-center gap-2">
              <span className="rounded border border-zinc-700 bg-zinc-800/70 px-1.5 py-0.5 font-mono text-[10px] text-cyan-300">
                {t.ruleId}
              </span>
              <span className="truncate text-zinc-400" title={t.label}>
                {t.label.replace(/^R\d+\s*/, "").replace(/\s*\([^)]*\)$/, "")}
              </span>
            </span>
            <span className="shrink-0 tabular-nums text-zinc-500">
              {t.count}× · {t.projects.size}p
            </span>
          </div>
          <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-zinc-800">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-violet-500"
              initial={{ width: 0 }}
              animate={{ width: `${(t.count / max) * 100}%` }}
              transition={{ duration: 0.6, ease: "easeOut" }}
            />
          </div>
        </motion.div>
      ))}
    </div>
  );
}
