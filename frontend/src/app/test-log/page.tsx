"use client";

import { useState } from "react";
import { FlaskConical } from "lucide-react";

import { AnalysisResult as AnalysisResultType } from "@/types/analysis";
import AnalysisResult from "@/app/analysis/AnalysisResult";
import { analyzeTestLogs } from "@/lib/api/analysis";
import { AppShell } from "@/app/components/Layout/AppShell";

type Strategy = "rule" | "gpt";

export default function TestLogPage() {
  const [input, setInput] = useState("");
  const [strategy, setStrategy] = useState<Strategy>("rule");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResultType | null>(null);
  const [error, setError] = useState<string | null>(null);

  const analyze = async () => {
    if (!input.trim() || loading) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const messages = input
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean);

      const data = await analyzeTestLogs(messages, strategy);
      setResult(data);
    } catch (e) {
      console.error(e);
      setError("분석 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      {/* ================= Main ================= */}
      <main className="mx-auto max-w-5xl space-y-10 px-8 py-10">
        {/* Header */}
        <header className="flex items-center gap-3">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-2.5 text-emerald-400">
            <FlaskConical size={22} />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Test Log Analysis
            </h1>
            <p className="text-sm text-zinc-400">
              테스트 로그를 즉시 분석합니다 · DB 저장 ❌
            </p>
          </div>
        </header>

        {/* ================= Input Card ================= */}
        <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-6 space-y-6">
          {/* Strategy Tabs */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-zinc-300">
              Analysis Strategy
            </span>

            <div className="flex rounded-lg border border-zinc-700 overflow-hidden">
              {(["rule", "gpt"] as Strategy[]).map((s) => (
                <button
                  key={s}
                  onClick={() => setStrategy(s)}
                  className={`px-4 py-2 text-sm font-semibold transition
                    ${
                      strategy === s
                        ? s === "rule"
                          ? "bg-emerald-600 text-white"
                          : "bg-indigo-600 text-white"
                        : "bg-zinc-900 text-zinc-400 hover:bg-zinc-800"
                    }
                  `}
                >
                  {s.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {/* Raw Logs */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-zinc-300">
              Raw Logs
            </label>

            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`ERROR gateway Request timed out after 30s
WARN nginx upstream response delayed
INFO healthcheck ok`}
              className="
                w-full h-44 resize-none
                bg-zinc-950 border border-zinc-800
                rounded-lg p-4 text-sm leading-relaxed
                placeholder:text-zinc-600
                focus:outline-none focus:ring-1 focus:ring-emerald-500
              "
            />
          </div>

          {/* Action */}
          <div className="flex items-center justify-between">
            <button
              onClick={analyze}
              disabled={loading}
              className="
                inline-flex items-center gap-2
                px-6 py-3 rounded-lg
                bg-emerald-600 hover:bg-emerald-500
                disabled:opacity-50
                text-white font-semibold
                transition
              "
            >
              {loading ? "Analyzing..." : "Analyze"}
            </button>

            {error && <span className="text-sm text-red-400">{error}</span>}
          </div>
        </section>

        {/* ================= Result ================= */}
        {result && (
          <section className="space-y-4">
            <AnalysisResult result={result} />
          </section>
        )}
      </main>
    </AppShell>
  );
}
