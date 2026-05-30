"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import {
  Plus,
  Trash2,
  Play,
  Search,
  ScrollText,
  RefreshCw,
} from "lucide-react";

import { fetchLogs, createLog, deleteLog } from "@/lib/api/log";
import { analyzeLogs } from "@/lib/api/analysis";
import { useProjectLiveRefresh } from "@/lib/useLiveEvents";
import type { LogItem, LogLevel } from "@/types/log";
import type { AnalysisResult as AnalysisResultType } from "@/types/analysis";
import { Card } from "@/app/components/ui/Card";
import AnalysisResult from "@/app/analysis/AnalysisResult";

const LEVELS: LogLevel[] = ["DEBUG", "INFO", "WARN", "ERROR"];
type CreateLevel = "INFO" | "WARN" | "ERROR";
const CREATE_LEVELS: CreateLevel[] = ["INFO", "WARN", "ERROR"];

const LEVEL_STYLE: Record<string, string> = {
  ERROR: "bg-red-500/20 text-red-400",
  WARN: "bg-amber-500/20 text-amber-400",
  INFO: "bg-cyan-500/20 text-cyan-400",
  DEBUG: "bg-zinc-700/40 text-zinc-400",
};

export default function ProjectLogsTab() {
  const { projectId } = useParams() as { projectId: string };

  const [logs, setLogs] = useState<LogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [levelFilter, setLevelFilter] = useState<LogLevel | "ALL">("ALL");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<{ source: string; level: CreateLevel; message: string }>({
    source: "",
    level: "ERROR",
    message: "",
  });

  const [strategy, setStrategy] = useState<"rule" | "gpt">("rule");
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResultType | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setLogs(await fetchLogs(projectId).catch(() => []));
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) load();
  }, [projectId, load]);

  // 실시간: 이 프로젝트로 인입되면 자동 갱신
  useProjectLiveRefresh(projectId, load);

  const filtered = useMemo(() => {
    return logs.filter((l) => {
      if (levelFilter !== "ALL" && l.level !== levelFilter) return false;
      if (search && !`${l.source} ${l.message}`.toLowerCase().includes(search.toLowerCase()))
        return false;
      return true;
    });
  }, [logs, levelFilter, search]);

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const toggleAll = () =>
    setSelected((prev) =>
      prev.size === filtered.length ? new Set() : new Set(filtered.map((l) => l.id))
    );

  const addLog = async () => {
    if (!form.source.trim() || !form.message.trim()) return;
    await createLog(projectId, form);
    setForm({ source: "", level: "ERROR", message: "" });
    setShowForm(false);
    await load();
  };

  const removeLog = async (id: string) => {
    await deleteLog(projectId, id);
    setSelected((p) => {
      const n = new Set(p);
      n.delete(id);
      return n;
    });
    setLogs((p) => p.filter((l) => l.id !== id));
  };

  const runAnalysis = async () => {
    const ids = selected.size ? [...selected] : filtered.map((l) => l.id);
    if (ids.length === 0) return;
    setAnalyzing(true);
    setResult(null);
    try {
      const data = await analyzeLogs(projectId, ids, strategy);
      setResult(data as AnalysisResultType);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900/60 p-1">
          {(["ALL", ...LEVELS] as const).map((lv) => (
            <button
              key={lv}
              onClick={() => setLevelFilter(lv)}
              className={
                "rounded-md px-2.5 py-1 text-xs font-medium transition-colors " +
                (levelFilter === lv
                  ? "bg-zinc-700 text-white"
                  : "text-zinc-400 hover:text-zinc-100")
              }
            >
              {lv}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-1.5">
          <Search size={14} className="text-zinc-500" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="source / message 검색"
            className="w-44 bg-transparent text-sm text-zinc-200 outline-none placeholder:text-zinc-600"
          />
        </div>

        <button
          onClick={() => setShowForm((s) => !s)}
          className="flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-1.5 text-sm text-zinc-300 hover:border-cyan-700 hover:text-cyan-300"
        >
          <Plus size={15} /> 로그 추가
        </button>

        <button
          onClick={load}
          className="flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-1.5 text-sm text-zinc-400 hover:text-zinc-100"
        >
          <RefreshCw size={14} />
        </button>

        {/* Analyze action */}
        <div className="ml-auto flex items-center gap-2">
          <div className="flex overflow-hidden rounded-lg border border-zinc-700">
            {(["rule", "gpt"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setStrategy(s)}
                className={
                  "px-3 py-1.5 text-xs font-semibold transition-colors " +
                  (strategy === s
                    ? s === "rule"
                      ? "bg-emerald-600 text-white"
                      : "bg-indigo-600 text-white"
                    : "bg-zinc-900 text-zinc-400 hover:bg-zinc-800")
                }
              >
                {s.toUpperCase()}
              </button>
            ))}
          </div>
          <button
            onClick={runAnalysis}
            disabled={analyzing}
            className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-violet-500 px-4 py-1.5 text-sm font-semibold text-zinc-950 transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            <Play size={14} />
            {analyzing
              ? "분석 중…"
              : selected.size
              ? `선택 ${selected.size}건 분석`
              : "전체 분석"}
          </button>
        </div>
      </div>

      {/* Add form */}
      {showForm && (
        <Card>
          <div className="grid gap-3 sm:grid-cols-[140px_120px_1fr_auto]">
            <input
              value={form.source}
              onChange={(e) => setForm({ ...form, source: e.target.value })}
              placeholder="source (예: gateway)"
              className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-cyan-600"
            />
            <select
              value={form.level}
              onChange={(e) => setForm({ ...form, level: e.target.value as CreateLevel })}
              className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-cyan-600"
            >
              {CREATE_LEVELS.map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </select>
            <input
              value={form.message}
              onChange={(e) => setForm({ ...form, message: e.target.value })}
              placeholder="message"
              className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-cyan-600"
            />
            <button
              onClick={addLog}
              className="rounded-lg bg-zinc-800 px-4 py-2 text-sm font-medium text-zinc-100 hover:bg-zinc-700"
            >
              추가
            </button>
          </div>
        </Card>
      )}

      {/* Result */}
      {result && <AnalysisResult result={result} />}

      {/* Log table */}
      <Card title={`Logs (${filtered.length})`} icon={<ScrollText size={16} className="text-cyan-400" />}>
        {loading ? (
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-10 animate-pulse rounded-lg bg-zinc-800/40" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-12 text-center">
            <ScrollText size={28} className="text-zinc-600" />
            <p className="text-sm text-zinc-500">로그가 없습니다.</p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-zinc-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-900/60 text-xs text-zinc-500">
                <tr>
                  <th className="w-10 px-3 py-2">
                    <input
                      type="checkbox"
                      checked={selected.size > 0 && selected.size === filtered.length}
                      onChange={toggleAll}
                      className="accent-cyan-500"
                    />
                  </th>
                  <th className="px-3 py-2">Level</th>
                  <th className="px-3 py-2">Source</th>
                  <th className="px-3 py-2">Message</th>
                  <th className="px-3 py-2 text-right">Time</th>
                  <th className="w-10 px-3 py-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/70">
                {filtered.map((l) => (
                  <tr key={l.id} className="hover:bg-zinc-900/40">
                    <td className="px-3 py-2">
                      <input
                        type="checkbox"
                        checked={selected.has(l.id)}
                        onChange={() => toggle(l.id)}
                        className="accent-cyan-500"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <span className={"rounded px-1.5 py-0.5 text-[10px] font-semibold " + (LEVEL_STYLE[l.level] ?? LEVEL_STYLE.DEBUG)}>
                        {l.level}
                      </span>
                    </td>
                    <td className="px-3 py-2 font-mono text-xs text-zinc-400">{l.source}</td>
                    <td className="max-w-md truncate px-3 py-2 text-zinc-200" title={l.message}>
                      {l.message}
                    </td>
                    <td className="px-3 py-2 text-right text-xs text-zinc-500">
                      {new Date(l.timestamp).toLocaleString()}
                    </td>
                    <td className="px-3 py-2">
                      <button
                        onClick={() => removeLog(l.id)}
                        className="text-zinc-600 transition-colors hover:text-rose-400"
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
