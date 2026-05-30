"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { Activity, AlertTriangle, Boxes, Gauge, LineChart, Layers, ScrollText } from "lucide-react";

import { fetchLogs } from "@/lib/api/log";
import {
  fetchReports,
  fetchWeeklyReport,
  fetchConfidenceTrend,
  type ReportSummary,
  type WeeklyReport,
  type TrendPoint,
} from "@/lib/api/report";
import type { LogItem } from "@/types/log";
import type { Severity } from "@/types/analysis";
import {
  SEVERITY_ORDER,
  asSeverity,
  severityConfig,
} from "@/styles/severity";

import { Card } from "@/app/components/ui/Card";
import { ConfidenceTrendChart } from "@/app/components/charts/ConfidenceTrendChart";
import { ConfidenceGauge } from "@/app/components/charts/ConfidenceGauge";
import { SeverityDonut } from "@/app/components/charts/SeverityDonut";
import { KpiCard } from "@/app/dashboard/components/KpiCard";
import { RecentAnalyses } from "@/app/dashboard/components/RecentAnalyses";
import { WeeklyHero } from "@/app/dashboard/components/WeeklyHero";
import { LogActivity } from "./components/LogActivity";

export default function ProjectOverviewTab() {
  const { projectId } = useParams() as { projectId: string };

  const [logs, setLogs] = useState<LogItem[]>([]);
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [weekly, setWeekly] = useState<WeeklyReport | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [lg, rs, tr, wk] = await Promise.all([
        fetchLogs(projectId).catch(() => []),
        fetchReports(projectId, { limit: 30 }).catch(() => []),
        fetchConfidenceTrend(projectId).catch(() => ({ metric: "", points: [] })),
        fetchWeeklyReport(projectId).catch(() => null),
      ]);
      setLogs(lg);
      setReports(rs);
      setTrend(tr.points);
      setWeekly(wk);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) load();
  }, [projectId, load]);

  const { logs24h, errorRate } = useMemo(() => {
    const since = Date.now() - 24 * 60 * 60 * 1000;
    const recent = logs.filter((l) => new Date(l.timestamp).getTime() >= since);
    const errs = recent.filter((l) => l.level === "ERROR").length;
    return {
      logs24h: recent.length,
      errorRate: recent.length ? errs / recent.length : 0,
    };
  }, [logs]);

  const severityCounts = useMemo(() => {
    const base = Object.fromEntries(
      SEVERITY_ORDER.map((s) => [s, 0])
    ) as Record<Severity, number>;
    for (const r of reports) base[asSeverity(r.severity)] += 1;
    return base;
  }, [reports]);

  const last = reports[0];
  const lastConfidence = last?.confidence ?? 0;
  const lastSeverity = asSeverity(last?.severity);

  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="h-28 animate-pulse rounded-2xl border border-zinc-800 bg-zinc-900/40"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* KPI row */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard index={0} icon={Activity} label="Logs · 24h" value={logs24h} accent="#22d3ee" hint="최근 24시간" />
        <KpiCard index={1} icon={AlertTriangle} label="Error rate · 24h" value={errorRate * 100} decimals={1} suffix="%" accent="#fbbf24" hint="ERROR / 전체" />
        <KpiCard index={2} icon={Gauge} label="Last confidence" value={lastConfidence * 100} suffix="%" accent={severityConfig[lastSeverity].hex} hint={`severity · ${severityConfig[lastSeverity].label}`} />
        <KpiCard index={3} icon={Layers} label="Analyses" value={reports.length} accent="#a78bfa" hint="저장된 분석 수" />
      </section>

      {/* Log activity leads the project view (vs the fleet/issue dashboard) */}
      <Card title="Log Activity" icon={<ScrollText size={16} className="text-cyan-400" />}>
        <LogActivity logs={logs} />
      </Card>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card title="Confidence Trend" icon={<LineChart size={16} className="text-cyan-400" />}>
            {trend.length > 0 ? (
              <ConfidenceTrendChart points={trend} />
            ) : (
              <div className="flex h-[300px] flex-col items-center justify-center gap-2 text-center">
                <LineChart size={28} className="text-zinc-600" />
                <p className="text-sm text-zinc-500">트렌드 데이터가 아직 없습니다.</p>
              </div>
            )}
          </Card>

          <Card title="Recent Analyses" icon={<Activity size={16} className="text-sky-400" />}>
            <RecentAnalyses reports={reports.slice(0, 6)} projectId={projectId} />
          </Card>
        </div>

        <div className="space-y-6">
          <Card title="Latest Confidence" icon={<Gauge size={16} className="text-emerald-400" />}>
            <ConfidenceGauge value={lastConfidence} />
          </Card>
          <Card title="Severity Distribution" icon={<Boxes size={16} className="text-amber-400" />}>
            {reports.length > 0 ? (
              <>
                <SeverityDonut counts={severityCounts} />
                <div className="mt-3 flex flex-wrap justify-center gap-3">
                  {SEVERITY_ORDER.map((s) => (
                    <span key={s} className="flex items-center gap-1.5 text-xs text-zinc-400">
                      <span className="h-2.5 w-2.5 rounded-full" style={{ background: severityConfig[s].hex }} />
                      {severityConfig[s].label}
                      <b className="text-zinc-200">{severityCounts[s]}</b>
                    </span>
                  ))}
                </div>
              </>
            ) : (
              <div className="flex h-[220px] items-center justify-center text-sm text-zinc-500">데이터 없음</div>
            )}
          </Card>
        </div>
      </section>

      <WeeklyHero weekly={weekly} />
    </div>
  );
}
