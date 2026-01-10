"use client";

import { useEffect, useState } from "react";

import TopNav from "@/app/components/Layout/TopNav";
import LogForm from "@/app/logs/LogForm";
import LogList from "@/app/logs/LogList";
import LogFilter from "@/app/logs/LogFilter";
import StrategySelect from "@/app/analysis/StrategySelect";
import AnalysisResult from "@/app/analysis/AnalysisResult";
import AgentStatus from "@/app/logs/AgentStatus";

import { createLog, fetchLogs } from "@/lib/api/log";
import { analyzeLogs } from "@/lib/api/analysis";

import { Log, LogLevel } from "@/types/log";
import {
  AnalysisResult as AnalysisResultType,
  Strategy,
} from "@/types/analysis";

export default function Home() {
  // ===== context (임시 하드코딩, 추후 프로젝트 선택으로 교체) =====
  const tenantId = "test1";
  const projectId = "demo";

  // ===== state =====
  const [logs, setLogs] = useState<Log[]>([]);
  const [filter, setFilter] = useState<LogLevel | "ALL">("ALL");
  const [strategy, setStrategy] = useState<Strategy>("rule");
  const [analysisResult, setAnalysisResult] =
    useState<AnalysisResultType | null>(null);
  const [loading, setLoading] = useState(false);

  // ===== fetch logs (Agent → UI) =====
  useEffect(() => {
    const loadLogs = async () => {
      try {
        const data = await fetchLogs(tenantId, projectId);
        setLogs(data);
      } catch (e) {
        console.error("Failed to fetch logs", e);
      }
    };

    loadLogs(); // initial load

    // 🔁 polling (Agent용)
    const interval = setInterval(loadLogs, 3000);
    return () => clearInterval(interval);
  }, [tenantId, projectId]);

  // ===== handlers =====

  // 수동 로그 추가 (PoC / 테스트용)
  const handleAddLog = async (payload: {
    source: string;
    message: string;
    level: LogLevel;
    timestamp: string;
  }) => {
    try {
      await createLog(payload, tenantId, projectId);
      const data = await fetchLogs(tenantId, projectId);
      setLogs(data);
    } catch (e) {
      console.error("Failed to create log", e);
      alert("Failed to create log. Check backend server.");
    }
  };

  // 분석 실행
  const handleAnalyze = async () => {
    if (logs.length === 0 || loading) return;

    setLoading(true);
    setAnalysisResult(null);

    try {
      const logIds = logs.map((log) => log.id);
      const result = await analyzeLogs(logIds, strategy, tenantId, projectId);
      setAnalysisResult(result);
    } catch (e) {
      console.error("Failed to analyze logs", e);
      alert("Analysis failed. Check backend logs.");
    } finally {
      setLoading(false);
    }
  };

  const lastSeen =
    logs.length > 0
      ? new Date(logs[logs.length - 1].received_at).toLocaleTimeString()
      : undefined;

  // ===== derived =====
  const filteredLogs =
    filter === "ALL" ? logs : logs.filter((l) => l.level === filter);

  // ===== render =====
  return (
    <>
      {/* Top navigation */}
      <TopNav />

      <main className="max-w-3xl mx-auto p-6 space-y-6">
        {/* Header */}
        <header className="space-y-1">
          <h1 className="text-2xl font-bold">NETSCOPE AI</h1>
          <p className="text-sm text-zinc-400">
            Explainable Network Log Analysis
          </p>

          {/* Agent status */}
          <AgentStatus connected={logs.length > 0} lastSeen={lastSeen} />
        </header>

        {/* Log filter */}
        <LogFilter value={filter} onChange={setFilter} />

        {/* Incoming logs */}
        {filteredLogs.length === 0 ? (
          <div className="text-sm text-zinc-500 text-center py-6">
            표시할 로그가 없습니다.
          </div>
        ) : (
          <LogList logs={filteredLogs} />
        )}

        {/* Manual log input (secondary) */}
        <section className="opacity-80">
          <h3 className="text-xs text-zinc-500 mb-2">
            Manual Log (testing only)
          </h3>
          <LogForm onAdd={handleAddLog} />
        </section>

        {/* Strategy */}
        <StrategySelect value={strategy} onChange={setStrategy} />

        {/* Analyze */}
        <button
          onClick={handleAnalyze}
          disabled={logs.length === 0 || loading}
          className="
            w-full bg-emerald-600 hover:bg-emerald-500
            disabled:opacity-40 disabled:cursor-not-allowed
            text-white py-3 rounded text-lg font-semibold
          "
        >
          {loading ? "Analyzing..." : `Analyze (${logs.length} logs)`}
        </button>

        {/* Result */}
        <AnalysisResult result={analysisResult} />
      </main>
    </>
  );
}
