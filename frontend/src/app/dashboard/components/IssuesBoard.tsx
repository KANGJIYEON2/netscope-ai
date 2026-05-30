"use client";

import Link from "next/link";
import { motion } from "framer-motion";

import type { Severity } from "@/types/analysis";
import { severityConfig, asSeverity } from "@/styles/severity";
import { timeAgo, ruleIdOf } from "@/lib/time";
import type { FleetIssue } from "./useFleetData";

// Triage order: most severe first.
const COLUMNS: Severity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];

function IssueCard({ issue, index }: { issue: FleetIssue; index: number }) {
  const cfg = severityConfig[asSeverity(issue.severity)];
  const topRule = issue.matched_rules?.[0];
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.03, duration: 0.3 }}
    >
      <Link
        href={`/projects/${issue.projectId}/analyses`}
        className="block rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 transition-colors hover:border-zinc-700 hover:bg-zinc-900"
        style={{ borderLeft: `3px solid ${cfg.hex}` }}
      >
        <div className="flex items-center justify-between gap-2">
          <span className="truncate text-[11px] font-medium text-zinc-400">
            {issue.projectName}
          </span>
          <span className="shrink-0 text-[10px] text-zinc-600">
            {timeAgo(issue.received_at)}
          </span>
        </div>
        <p className="mt-1 line-clamp-2 text-xs leading-snug text-zinc-200">
          {issue.summary}
        </p>
        <div className="mt-2 flex items-center gap-2">
          <span className="text-[11px] font-semibold tabular-nums" style={{ color: cfg.hex }}>
            {Math.round(issue.confidence * 100)}%
          </span>
          {topRule && (
            <span className="rounded border border-zinc-700 bg-zinc-800/70 px-1.5 py-0.5 font-mono text-[9px] text-zinc-300">
              {ruleIdOf(topRule)}
            </span>
          )}
        </div>
      </Link>
    </motion.div>
  );
}

export function IssuesBoard({ issues }: { issues: FleetIssue[] }) {
  const grouped = COLUMNS.map((sev) => ({
    sev,
    items: issues.filter((i) => asSeverity(i.severity) === sev),
  }));

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {grouped.map(({ sev, items }) => {
        const cfg = severityConfig[sev];
        return (
          <div
            key={sev}
            className="flex flex-col rounded-xl border border-zinc-800/70 bg-zinc-950/40"
          >
            <div
              className="flex items-center justify-between rounded-t-xl border-b border-zinc-800 px-3 py-2"
              style={{ background: `${cfg.hex}14` }}
            >
              <span className="flex items-center gap-1.5 text-xs font-semibold" style={{ color: cfg.hex }}>
                <span className="h-2 w-2 rounded-full" style={{ background: cfg.hex }} />
                {cfg.label}
              </span>
              <span className="rounded-full bg-zinc-800 px-1.5 text-[10px] font-bold text-zinc-300">
                {items.length}
              </span>
            </div>
            <div className="max-h-[420px] space-y-2 overflow-y-auto p-2">
              {items.length === 0 ? (
                <p className="py-6 text-center text-[11px] text-zinc-600">—</p>
              ) : (
                items.slice(0, 12).map((issue, i) => (
                  <IssueCard key={`${issue.projectId}-${i}`} issue={issue} index={i} />
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
