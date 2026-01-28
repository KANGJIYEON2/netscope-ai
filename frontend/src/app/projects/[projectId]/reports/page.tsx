"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

import {
  fetchReports,
  fetchWeeklyReport,
  WeeklyReport,
  ReportSummary,
} from "@/lib/api/report";
import { fetchLogs } from "@/lib/api/log";
import { LogItem } from "@/types/log";
import { analyzeLogs } from "@/lib/api/analysis";
import WeeklyReportCard from "../components/WeeklyReportCard";

export default function ProjectReportsPage() {
  const params = useParams();
  const projectId = params?.projectId as string | undefined;

  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [weekly, setWeekly] = useState<WeeklyReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);

  const load = async () => {
    if (!projectId) return;

    setLoading(true);

    try {
      const list = await fetchReports(projectId, { limit: 20 });
      setReports(list);

      try {
        const w = await fetchWeeklyReport(projectId);
        setWeekly(w);
      } catch {
        setWeekly(null);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!projectId) return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  /** 🔥 최근 7일 로그 → 분석 실행 */
  const runWeeklyAnalysis = async () => {
    if (!projectId) return;

    setAnalyzing(true);

    try {
      // 1️⃣ 로그 조회
      const logs: LogItem[] = await fetchLogs(projectId);

      // 2️⃣ 최근 7일 필터
      const since = Date.now() - 7 * 24 * 60 * 60 * 1000;
      const logIds = logs
        .filter((l) => new Date(l.timestamp).getTime() >= since)
        .map((l) => l.id);

      if (logIds.length === 0) {
        alert("최근 7일간 분석할 로그가 없습니다.");
        return;
      }

      // 3️⃣ 분석 실행
      await analyzeLogs(projectId, logIds, "rule");

      // 4️⃣ 새로고침
      await load();
    } catch (e) {
      // ✅ 401이면 apiClient 인터셉터가 refresh 후 실패 시 /auth/login 이동
      console.error("Weekly analysis failed", e);
      alert("분석 실행 실패");
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center text-zinc-400">
        Loading...
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-zinc-950 text-white">
      {/* Left Nav */}
      <aside className="w-56 border-r border-zinc-800 p-4">
        <nav className="space-y-2">
          <Link
            href="/test-log"
            className="block px-3 py-2 text-sm text-zinc-400"
          >
            Test Log
          </Link>
          <Link
            href="/projects"
            className="block px-3 py-2 text-sm bg-zinc-800"
          >
            Project Log
          </Link>
        </nav>
      </aside>

      {/* Main */}
      <main className="flex-1 max-w-6xl mx-auto p-6 space-y-8">
        <header className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">Project Reports</h1>

          <button
            onClick={runWeeklyAnalysis}
            disabled={analyzing}
            className="
              px-4 py-2 rounded bg-indigo-600 hover:bg-indigo-500
              text-sm font-semibold disabled:opacity-50
            "
          >
            {analyzing ? "Analyzing..." : "최근 7일 분석 실행"}
          </button>
        </header>

        {/* Weekly */}
        {weekly ? (
          <WeeklyReportCard report={weekly} />
        ) : (
          <div className="border border-dashed border-zinc-700 rounded p-6 text-sm text-zinc-400">
            아직 생성된 주간 리포트가 없습니다.
          </div>
        )}

        {/* Report List */}
        <section className="space-y-3">
          {reports.map((r, i) => (
            <div
              key={i}
              className="rounded-lg border border-zinc-800 bg-zinc-900 p-4"
            >
              <p className="font-semibold">{r.summary}</p>
              <div className="flex justify-between text-xs text-zinc-500">
                <span>{r.severity}</span>
                <span>{(r.confidence * 100).toFixed(0)}%</span>
                <span>{r.strategy_used.toUpperCase()}</span>
                <span>{new Date(r.received_at).toLocaleString()}</span>
              </div>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}
