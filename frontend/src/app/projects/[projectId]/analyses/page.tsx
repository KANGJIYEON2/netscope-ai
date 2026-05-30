"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Activity, LineChart, Play } from "lucide-react";

import {
  fetchReports,
  fetchWeeklyReport,
  fetchConfidenceTrend,
  type ReportSummary,
  type WeeklyReport,
  type TrendPoint,
} from "@/lib/api/report";
import { fetchLogs } from "@/lib/api/log";
import { analyzeLogs } from "@/lib/api/analysis";
import { useProjectLiveRefresh } from "@/lib/useLiveEvents";
import { Card } from "@/app/components/ui/Card";
import { ConfidenceTrendChart } from "@/app/components/charts/ConfidenceTrendChart";
import { RecentAnalyses } from "@/app/dashboard/components/RecentAnalyses";
import { WeeklyHero } from "@/app/dashboard/components/WeeklyHero";

export default function ProjectAnalysesTab() {
  const { projectId } = useParams() as { projectId: string };

  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [weekly, setWeekly] = useState<WeeklyReport | null>(null);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [rs, wk, tr] = await Promise.all([
        fetchReports(projectId, { limit: 50 }).catch(() => []),
        fetchWeeklyReport(projectId).catch(() => null),
        fetchConfidenceTrend(projectId).catch(() => ({ metric: "", points: [] })),
      ]);
      setReports(rs);
      setWeekly(wk);
      setTrend(tr.points);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) load();
  }, [projectId, load]);

  // 실시간: 이 프로젝트의 새 분석이 들어오면 자동 갱신
  useProjectLiveRefresh(projectId, load);

  const runWeekly = async () => {
    setRunning(true);
    try {
      const logs = await fetchLogs(projectId);
      const since = Date.now() - 7 * 24 * 60 * 60 * 1000;
      const ids = logs
        .filter((l) => new Date(l.timestamp).getTime() >= since)
        .map((l) => l.id);
      if (ids.length === 0) {
        alert("최근 7일간 분석할 로그가 없습니다.");
        return;
      }
      await analyzeLogs(projectId, ids, "rule");
      await load();
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <WeeklyHero weekly={weekly} />

      <Card
        title="Confidence Trend"
        icon={<LineChart size={16} className="text-cyan-400" />}
        action={
          <button
            onClick={runWeekly}
            disabled={running}
            className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-violet-500 px-3 py-1.5 text-xs font-semibold text-zinc-950 transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            <Play size={13} /> {running ? "분석 중…" : "최근 7일 분석 실행"}
          </button>
        }
      >
        {trend.length > 0 ? (
          <ConfidenceTrendChart points={trend} />
        ) : (
          <div className="flex h-[280px] flex-col items-center justify-center gap-2 text-center">
            <LineChart size={28} className="text-zinc-600" />
            <p className="text-sm text-zinc-500">트렌드 데이터가 아직 없습니다.</p>
          </div>
        )}
      </Card>

      <Card
        title={`Analyses (${reports.length})`}
        icon={<Activity size={16} className="text-sky-400" />}
      >
        {loading ? (
          <div className="space-y-2.5">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-14 animate-pulse rounded-xl bg-zinc-800/40" />
            ))}
          </div>
        ) : (
          <RecentAnalyses reports={reports} projectId={projectId} />
        )}
      </Card>
    </div>
  );
}
