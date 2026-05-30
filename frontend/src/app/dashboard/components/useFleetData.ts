"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { fetchProjects, type ProjectItem } from "@/lib/api/project";
import { fetchProjectOverview, type ProjectOverview } from "@/lib/api/overview";
import { fetchReports, type ReportSummary } from "@/lib/api/report";
import type { Severity } from "@/types/analysis";
import { asSeverity } from "@/styles/severity";
import { useLiveEvents, type LiveEvent } from "@/lib/useLiveEvents";

export type FleetIssue = ReportSummary & {
  projectId: string;
  projectName: string;
};

export type ProjectHealth = {
  project: ProjectItem;
  issues: FleetIssue[];
  lastSeverity: Severity;
  lastConfidence: number;
  lastAt: string | null;
  openCount: number; // HIGH + CRITICAL
};

export type FleetData = {
  projects: ProjectItem[];
  overview: ProjectOverview | null;
  health: ProjectHealth[];
  issues: FleetIssue[]; // all, newest first
  loading: boolean;
  lastUpdated: number;
};

const EMPTY: FleetData = {
  projects: [],
  overview: null,
  health: [],
  issues: [],
  loading: true,
  lastUpdated: 0,
};

/**
 * Fleet-wide aggregation across every project (issue-centric, real-time).
 * Fans out per-project report fetches and re-polls on an interval so the
 * global dashboard feels live.
 */
export function useFleetData(pollMs = 30000) {
  const [data, setData] = useState<FleetData>(EMPTY);
  const [liveEvent, setLiveEvent] = useState<LiveEvent | null>(null);
  const alive = useRef(true);
  const debounce = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadOnce = useCallback(async (silent: boolean) => {
    if (!silent) setData((d) => ({ ...d, loading: true }));

    const [projects, overview] = await Promise.all([
      fetchProjects().catch(() => [] as ProjectItem[]),
      fetchProjectOverview().catch(() => null),
    ]);

    const perProject = await Promise.all(
      projects.map(async (p) => {
        const reports = await fetchReports(p.id, { limit: 25 }).catch(
          () => [] as ReportSummary[]
        );
        const issues: FleetIssue[] = reports.map((r) => ({
          ...r,
          projectId: p.id,
          projectName: p.name,
        }));
        const last = issues[0];
        const health: ProjectHealth = {
          project: p,
          issues,
          lastSeverity: asSeverity(last?.severity),
          lastConfidence: last?.confidence ?? 0,
          lastAt: last?.received_at ?? null,
          openCount: issues.filter((i) => {
            const s = asSeverity(i.severity);
            return s === "HIGH" || s === "CRITICAL";
          }).length,
        };
        return health;
      })
    );

    const issues = perProject
      .flatMap((h) => h.issues)
      .sort(
        (a, b) =>
          new Date(b.received_at).getTime() - new Date(a.received_at).getTime()
      );

    if (!alive.current) return;
    setData({
      projects,
      overview,
      health: perProject,
      issues,
      loading: false,
      lastUpdated: Date.now(),
    });
  }, []);

  useEffect(() => {
    alive.current = true;
    // Initial fetch on mount. loadOnce is async — setState happens after the
    // awaited network calls, so this is data-fetching, not a synchronous
    // cascading render. The lint rule can't see across the async boundary.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadOnce(true);
    // Slow poll as a fallback; SSE drives the real-time updates below.
    const id = setInterval(() => loadOnce(true), pollMs);
    return () => {
      alive.current = false;
      clearInterval(id);
    };
  }, [loadOnce, pollMs]);

  // Real-time: refresh (debounced) whenever the backend pushes an event.
  useLiveEvents((evt) => {
    setLiveEvent(evt);
    if (debounce.current) clearTimeout(debounce.current);
    debounce.current = setTimeout(() => loadOnce(true), 400);
  });

  return { data, liveEvent, refresh: () => loadOnce(false) };
}
