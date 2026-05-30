"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowUpRight, AlertTriangle, Layers } from "lucide-react";

import { severityConfig } from "@/styles/severity";
import { timeAgo } from "@/lib/time";
import type { ProjectHealth } from "./useFleetData";

function HealthCard({ h, index }: { h: ProjectHealth; index: number }) {
  const cfg = severityConfig[h.lastSeverity];
  const pct = Math.round(h.lastConfidence * 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.4 }}
    >
      <Link
        href={`/projects/${h.project.id}`}
        className="group relative block overflow-hidden rounded-2xl border border-zinc-800/80 bg-zinc-900/50 p-5 transition-colors hover:border-zinc-700"
        style={{ borderLeft: `4px solid ${cfg.hex}` }}
      >
        <div
          className="pointer-events-none absolute -right-12 -top-12 h-32 w-32 rounded-full opacity-15 blur-2xl transition-opacity group-hover:opacity-30"
          style={{ background: cfg.hex }}
        />
        <div className="relative">
          <div className="flex items-start justify-between">
            <div className="min-w-0">
              <h3 className="truncate text-base font-semibold text-zinc-100">
                {h.project.name}
              </h3>
              <p className="mt-0.5 text-xs text-zinc-500">
                {h.lastAt ? `last · ${timeAgo(h.lastAt)}` : "분석 없음"}
              </p>
            </div>
            <span className={cfg.badge + " rounded-full px-2 py-0.5 text-[10px] font-semibold"}>
              {cfg.label}
            </span>
          </div>

          {/* confidence bar */}
          <div className="mt-4 flex items-center gap-2">
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-zinc-800">
              <div
                className="h-full rounded-full"
                style={{ width: `${pct}%`, background: cfg.hex }}
              />
            </div>
            <span className="text-xs font-semibold tabular-nums" style={{ color: cfg.hex }}>
              {pct}%
            </span>
          </div>

          <div className="mt-4 flex items-center gap-4 text-xs text-zinc-400">
            <span className="flex items-center gap-1">
              <Layers size={13} className="text-zinc-500" /> {h.issues.length} analyses
            </span>
            {h.openCount > 0 && (
              <span className="flex items-center gap-1 text-rose-300">
                <AlertTriangle size={13} /> {h.openCount} open
              </span>
            )}
            <ArrowUpRight
              size={16}
              className="ml-auto text-zinc-600 transition-colors group-hover:text-cyan-400"
            />
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

export function ProjectsHealthGrid({ health }: { health: ProjectHealth[] }) {
  if (health.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-zinc-800 py-12 text-center text-sm text-zinc-500">
        프로젝트가 없습니다.
      </div>
    );
  }
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {health.map((h, i) => (
        <HealthCard key={h.project.id} h={h} index={i} />
      ))}
    </div>
  );
}
