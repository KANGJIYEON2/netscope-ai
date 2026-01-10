"use client";

import { useState } from "react";
import { createLog } from "@/lib/api/log";

type Props = {
  projectId: string;
  onClose: () => void;
  onCreated?: () => void;
};

type LogLevel = "INFO" | "WARN" | "ERROR";

// source DTO 규칙
const SOURCE_REGEX = /^[a-zA-Z0-9_-]{2,50}$/;

export default function NewLogModal({ projectId, onClose, onCreated }: Props) {
  const [source, setSource] = useState("");
  const [message, setMessage] = useState("");
  const [level, setLevel] = useState<LogLevel>("INFO");

  // 🔥 과거 로그 입력용
  const [useCustomTime, setUseCustomTime] = useState(false);
  const [timestamp, setTimestamp] = useState<string>("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    if (!SOURCE_REGEX.test(source)) {
      setError("Source는 2~50자의 영문, 숫자, -, _ 만 가능합니다.");
      return;
    }

    if (!message.trim()) {
      setError("Message는 필수입니다.");
      return;
    }

    if (useCustomTime && !timestamp) {
      setError("과거 로그 시간을 선택해주세요.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await createLog(projectId, {
        source,
        message,
        level,
        ...(useCustomTime && {
          timestamp: new Date(timestamp).toISOString(),
        }),
      });

      onCreated?.();
      onClose();
    } catch (e) {
      console.error(e);
      setError("로그 저장 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-lg rounded-lg bg-zinc-950 border border-zinc-800 p-6 space-y-6 text-white">
        {/* Header */}
        <header className="space-y-1">
          <h2 className="text-lg font-bold">New Log</h2>
          <p className="text-xs text-zinc-400">
            수동 로그를 프로젝트에 저장합니다.
          </p>
        </header>

        {/* Source */}
        <div className="space-y-1">
          <label className="text-xs font-semibold text-zinc-300">Source</label>
          <input
            value={source}
            onChange={(e) => setSource(e.target.value)}
            placeholder="gateway, api-server, worker_1"
            className="w-full bg-zinc-900 border border-zinc-800 px-3 py-2 rounded text-sm"
          />
          <p className="text-[11px] text-zinc-500">
            영문 / 숫자 / - / _ · 2~50자
          </p>
        </div>

        {/* Level */}
        <div className="space-y-1">
          <label className="text-xs font-semibold text-zinc-300">
            Log Level
          </label>
          <select
            value={level}
            onChange={(e) => setLevel(e.target.value as LogLevel)}
            className="w-full bg-zinc-900 border border-zinc-800 px-3 py-2 rounded text-sm"
          >
            <option value="INFO">INFO</option>
            <option value="WARN">WARN</option>
            <option value="ERROR">ERROR</option>
          </select>
        </div>

        {/* Message */}
        <div className="space-y-1">
          <label className="text-xs font-semibold text-zinc-300">Message</label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="ERROR gateway Request timed out after 30s"
            className="w-full h-28 bg-zinc-900 border border-zinc-800 px-3 py-2 rounded text-sm"
          />
        </div>

        {/* 🔥 Timestamp */}
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-xs text-zinc-300">
            <input
              type="checkbox"
              checked={useCustomTime}
              onChange={(e) => setUseCustomTime(e.target.checked)}
            />
            과거 로그 입력
          </label>

          {useCustomTime && (
            <input
              type="datetime-local"
              value={timestamp}
              max={new Date().toISOString().slice(0, 16)}
              onChange={(e) => setTimestamp(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 px-3 py-2 rounded text-sm"
            />
          )}
        </div>

        {/* Error */}
        {error && <p className="text-xs text-red-400">{error}</p>}

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-2">
          <button
            onClick={onClose}
            className="text-sm text-zinc-400 hover:text-white"
          >
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={loading}
            className="px-4 py-2 bg-emerald-600 rounded text-sm font-semibold disabled:opacity-50"
          >
            {loading ? "Saving..." : "Save Log"}
          </button>
        </div>
      </div>
    </div>
  );
}
