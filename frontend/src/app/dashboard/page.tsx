"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  AlertOctagon,
  FolderGit2,
  Boxes,
  RefreshCw,
  Radio,
  LayoutGrid,
  Flame,
} from "lucide-react";

import { AppShell } from "@/app/components/Layout/AppShell";
import { Card } from "@/app/components/ui/Card";
import { asSeverity } from "@/styles/severity";
import { timeAgo } from "@/lib/time";

import { KpiCard } from "./components/KpiCard";
import { useFleetData } from "./components/useFleetData";
import { ProjectsHealthGrid } from "./components/ProjectsHealthGrid";
import { IssuesBoard } from "./components/IssuesBoard";
import { ActivityFeed } from "./components/ActivityFeed";
import { TopIssues } from "./components/TopIssues";

export default function FleetDashboardPage() {
  const { data, refresh } = useFleetData(15000);

  // 1s tick so the "updated Xs ago" label stays live.
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  const kpis = useMemo(() => {
    const open = data.issues.filter((i) => {
      const s = asSeverity(i.severity);
      return s === "HIGH" || s === "CRITICAL";
    }).length;
    const critical = data.issues.filter(
      (i) => asSeverity(i.severity) === "CRITICAL"
    ).length;
    return {
      projects: data.projects.length,
      open,
      critical,
      logs24h: data.overview?.log_count_24h ?? 0,
      errorRate: (data.overview?.error_rate ?? 0) * 100,
    };
  }, [data]);

  if (data.loading) {
    return (
      <AppShell>
        <div className="flex min-h-screen items-center justify-center">
          <div className="flex items-center gap-3 text-zinc-400">
            <RefreshCw className="animate-spin" size={18} />
            <span className="text-sm">Fleet 데이터 집계 중…</span>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <main className="relative mx-auto max-w-7xl px-5 py-8 sm:px-8">
        {/* Header */}
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-2.5 text-cyan-400">
              <Radio size={22} />
            </div>
            <div>
              <h1 className="bg-gradient-to-r from-cyan-300 via-sky-200 to-violet-300 bg-clip-text text-2xl font-bold text-transparent">
                Fleet Command
              </h1>
              <p className="text-xs text-zinc-500">
                전체 프로젝트 · 이슈 중심 실시간 진단
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 rounded-full border border-emerald-700/40 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
              </span>
              LIVE
            </span>
            <span className="hidden text-xs text-zinc-500 sm:block">
              updated {data.lastUpdated ? timeAgo(new Date(data.lastUpdated).toISOString()) : "—"}
            </span>
            <button
              onClick={refresh}
              className="flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-300 transition-colors hover:border-cyan-600 hover:text-cyan-300"
            >
              <RefreshCw size={15} /> 새로고침
            </button>
          </div>
        </header>

        {/* Fleet KPI strip */}
        <section className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          <KpiCard index={0} icon={FolderGit2} label="Projects" value={kpis.projects} accent="#38bdf8" hint="모니터링 중" />
          <KpiCard index={1} icon={AlertTriangle} label="Open issues" value={kpis.open} accent="#fbbf24" hint="HIGH + CRITICAL" />
          <KpiCard index={2} icon={AlertOctagon} label="Critical" value={kpis.critical} accent="#e879f9" hint="즉시 대응" />
          <KpiCard index={3} icon={Activity} label="Logs · 24h" value={kpis.logs24h} accent="#22d3ee" hint="테넌트 전체" />
          <KpiCard index={4} icon={Boxes} label="Error rate" value={kpis.errorRate} decimals={1} suffix="%" accent="#f87171" hint="24h" />
        </section>

        {/* Projects health grid */}
        <section className="mt-8">
          <div className="mb-4 flex items-center gap-2">
            <LayoutGrid size={16} className="text-cyan-400" />
            <h2 className="text-sm font-semibold text-zinc-200">Projects Health</h2>
            <span className="text-xs text-zinc-600">· 클릭하면 프로젝트 대시보드</span>
          </div>
          <ProjectsHealthGrid health={data.health} />
        </section>

        {/* Issues board (severity-grouped) */}
        <section className="mt-8">
          <div className="mb-4 flex items-center gap-2">
            <Flame size={16} className="text-amber-400" />
            <h2 className="text-sm font-semibold text-zinc-200">Issues Board</h2>
            <span className="text-xs text-zinc-600">· severity별 전사 이슈</span>
          </div>
          <IssuesBoard issues={data.issues} />
        </section>

        {/* Live feed + recurring issues */}
        <section className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <Card title="Live Activity" icon={<Radio size={16} className="text-emerald-400" />}>
              <ActivityFeed issues={data.issues} />
            </Card>
          </div>
          <Card title="Recurring Issues" icon={<Flame size={16} className="text-rose-400" />}>
            <TopIssues issues={data.issues} />
          </Card>
        </section>
      </main>
    </AppShell>
  );
}
