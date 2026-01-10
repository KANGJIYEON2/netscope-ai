"use client";

import { Strategy } from "@/types/analysis";

interface StrategySelectProps {
  value: Strategy;
  onChange: (value: Strategy) => void;
}

export default function StrategySelect({
  value,
  onChange,
}: StrategySelectProps) {
  return (
    <div className="border border-zinc-800 rounded-lg p-4 space-y-3">
      <h2 className="text-lg font-semibold">Analysis Strategy</h2>

      <div className="flex gap-3">
        {/* Rule */}
        <button
          type="button"
          onClick={() => onChange("rule")}
          className={`flex-1 px-4 py-2 rounded border transition ${
            value === "rule"
              ? "bg-zinc-800 border-zinc-600 text-white"
              : "bg-zinc-900 border-zinc-800 text-zinc-400 hover:bg-zinc-800"
          }`}
        >
          <div className="font-semibold">Rule</div>
          <div className="text-xs mt-1 opacity-80">Deterministic baseline</div>
        </button>

        {/* GPT */}
        <button
          type="button"
          onClick={() => onChange("gpt")}
          className={`flex-1 px-4 py-2 rounded border transition ${
            value === "gpt"
              ? "bg-indigo-600 border-indigo-500 text-white"
              : "bg-zinc-900 border-zinc-800 text-zinc-400 hover:bg-zinc-800"
          }`}
        >
          <div className="font-semibold">GPT</div>
          <div className="text-xs mt-1 opacity-80">Rule + LLM insight</div>
        </button>
      </div>
    </div>
  );
}
