"use client";

import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { Radio } from "lucide-react";

import { severityConfig, asSeverity } from "@/styles/severity";
import { timeAgo } from "@/lib/time";
import type { FleetIssue } from "./useFleetData";

/** Live cross-project activity stream (newest analyses first). */
export function ActivityFeed({ issues }: { issues: FleetIssue[] }) {
  const items = issues.slice(0, 14);

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-12 text-center">
        <Radio size={26} className="text-zinc-600" />
        <p className="text-sm text-zinc-500">활동 내역이 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <AnimatePresence initial={false}>
        {items.map((issue, i) => {
          const cfg = severityConfig[asSeverity(issue.severity)];
          return (
            <motion.div
              key={`${issue.projectId}-${issue.received_at}-${i}`}
              layout
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
            >
              <Link
                href={`/projects/${issue.projectId}/analyses`}
                className="flex items-start gap-3 rounded-lg px-2 py-2 transition-colors hover:bg-zinc-800/40"
              >
                <span
                  className="mt-1.5 h-2 w-2 shrink-0 rounded-full"
                  style={{ background: cfg.hex, boxShadow: `0 0 8px ${cfg.hex}` }}
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-xs font-medium text-zinc-300">
                      {issue.projectName}
                    </span>
                    <span className="shrink-0 text-[10px] text-zinc-600">
                      {timeAgo(issue.received_at)}
                    </span>
                  </div>
                  <p className="truncate text-xs text-zinc-500">{issue.summary}</p>
                </div>
                <span
                  className="shrink-0 text-[11px] font-semibold tabular-nums"
                  style={{ color: cfg.hex }}
                >
                  {Math.round(issue.confidence * 100)}%
                </span>
              </Link>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
