"use client";

import { useState } from "react";
import { LogLevel } from "@/types/log";

interface LogFormProps {
  onAdd: (payload: {
    source: string;
    message: string;
    level: LogLevel;
    timestamp: string;
  }) => void;
}

export default function LogForm({ onAdd }: LogFormProps) {
  const [source, setSource] = useState("");
  const [message, setMessage] = useState("");
  const [level, setLevel] = useState<LogLevel>("ERROR");

  const handleSubmit = () => {
    if (!source || !message) return;

    onAdd({
      source,
      message,
      level,
      timestamp: new Date().toISOString(),
    });

    setSource("");
    setMessage("");
    setLevel("ERROR");
  };

  return (
    <div className="border border-zinc-800 rounded-lg p-4 space-y-3 bg-zinc-950">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-zinc-300">Dev Test Log</h2>
        <span className="text-xs text-zinc-500">manual / local only</span>
      </div>

      <p className="text-xs text-zinc-500">
        This panel is for development testing only. In production, logs are
        collected automatically via agent.
      </p>

      {/* source */}
      <input
        className="
          w-full
          bg-zinc-900
          text-zinc-100
          placeholder-zinc-500
          border border-zinc-700
          rounded
          px-3 py-2
          focus:outline-none
          focus:ring-2 focus:ring-indigo-500
        "
        placeholder="source (e.g. gateway)"
        value={source}
        onChange={(e) => setSource(e.target.value)}
      />

      {/* message */}
      <textarea
        className="
          w-full
          bg-zinc-900
          text-zinc-100
          placeholder-zinc-500
          border border-zinc-700
          rounded
          px-3 py-2
          focus:outline-none
          focus:ring-2 focus:ring-indigo-500
        "
        placeholder="log message"
        rows={3}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
      />

      <div className="flex gap-3 items-center">
        {/* level */}
        <select
          className="
            bg-zinc-900
            text-zinc-100
            border border-zinc-700
            rounded
            px-3 py-2
            focus:outline-none
            focus:ring-2 focus:ring-indigo-500
          "
          value={level}
          onChange={(e) => setLevel(e.target.value as LogLevel)}
        >
          <option value="DEBUG">DEBUG</option>
          <option value="INFO">INFO</option>
          <option value="WARN">WARN</option>
          <option value="ERROR">ERROR</option>
        </select>

        {/* submit */}
        <button
          onClick={handleSubmit}
          className="
            ml-auto
            bg-zinc-700
            hover:bg-zinc-600
            text-white
            px-4 py-2
            rounded
            font-medium
            text-sm
          "
        >
          Send Test Log
        </button>
      </div>
    </div>
  );
}
