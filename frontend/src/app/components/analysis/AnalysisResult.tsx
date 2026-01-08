"use client";

import { AnalysisResult as AnalysisResultType } from "@/types/analysis";

interface AnalysisResultProps {
  result: AnalysisResultType | null;
}

const severityBadge: Record<AnalysisResultType["severity"], string> = {
  LOW: "bg-green-500/20 text-green-400",
  MEDIUM: "bg-yellow-500/20 text-yellow-400",
  HIGH: "bg-red-500/20 text-red-400",
};

export default function AnalysisResult({ result }: AnalysisResultProps) {
  if (!result) return null;

  return (
    <div className="border border-zinc-800 rounded-lg p-6 space-y-6 bg-zinc-950">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-zinc-100">Analysis Result</h2>
        <span className="text-xs text-zinc-400">
          strategy:{" "}
          <span className="font-semibold">{result.strategy_used}</span>
        </span>
      </div>

      {/* Severity */}
      <div className="flex items-center gap-4">
        <span
          className={`px-3 py-1 rounded-full text-sm font-bold ${
            severityBadge[result.severity]
          }`}
        >
          {result.severity}
        </span>

        <span className="text-sm text-zinc-400">
          Confidence{" "}
          <span className="font-semibold text-zinc-200">
            {(result.confidence * 100).toFixed(0)}%
          </span>
        </span>
      </div>

      {/* Summary */}
      <section className="space-y-2">
        <h3 className="text-sm font-semibold text-zinc-200">Summary</h3>
        <div className="bg-zinc-900 border border-zinc-800 rounded p-4">
          <p className="text-sm text-zinc-100 leading-relaxed whitespace-pre-line">
            {result.summary}
          </p>
        </div>
      </section>

      {/* Suspected Causes */}
      <section className="space-y-2">
        <h3 className="text-sm font-semibold text-zinc-200">
          Suspected Causes
        </h3>
        <ul className="list-disc pl-5 space-y-1 text-sm text-zinc-200">
          {result.suspected_causes.map((cause, idx) => (
            <li key={idx}>{cause}</li>
          ))}
        </ul>
      </section>

      {/* Recommended Actions */}
      <section className="space-y-2">
        <h3 className="text-sm font-semibold text-zinc-200">
          Recommended Actions
        </h3>
        <ul className="list-disc pl-5 space-y-1 text-sm text-zinc-200">
          {result.recommended_actions.map((action, idx) => (
            <li key={idx}>{action}</li>
          ))}
        </ul>
      </section>

      {/* Matched Rules */}
      <section className="space-y-2">
        <h3 className="text-sm font-semibold text-zinc-200">Matched Rules</h3>
        <ul className="space-y-2">
          {result.matched_rules.map((rule, idx) => (
            <li
              key={idx}
              className="text-xs text-zinc-300 bg-zinc-900 border border-zinc-800 rounded px-3 py-2"
            >
              {rule}
            </li>
          ))}
        </ul>
      </section>

      {/* Footer */}
      <div className="text-xs text-zinc-500 text-right">
        received at {new Date(result.received_at).toLocaleString()}
      </div>
    </div>
  );
}
