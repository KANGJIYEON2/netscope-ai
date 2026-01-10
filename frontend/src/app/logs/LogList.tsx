"use client";

import { LogItem } from "@/types/log";

interface LogListProps {
  logs: LogItem[];
  onRemove?: (id: string) => void;
}

export default function LogList({ logs }: LogListProps) {
  return (
    <div className="border border-zinc-800 rounded-lg bg-zinc-950 p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-zinc-300">Incoming Logs</h2>
        <span className="text-xs text-zinc-500">collected by agent</span>
      </div>

      {logs.length === 0 ? (
        <div className="text-xs text-zinc-500 py-6 text-center">
          Waiting for logs from agent…
        </div>
      ) : (
        <ul className="space-y-2 max-h-64 overflow-y-auto">
          {logs.map((log) => (
            <li
              key={log.id}
              className="border border-zinc-800 rounded p-3 text-xs bg-zinc-900"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-zinc-400">{log.source}</span>
                <span
                  className={`font-semibold ${
                    log.level === "ERROR"
                      ? "text-red-400"
                      : log.level === "WARN"
                      ? "text-yellow-400"
                      : "text-zinc-400"
                  }`}
                >
                  {log.level}
                </span>
              </div>

              <p className="text-zinc-200 whitespace-pre-wrap">{log.message}</p>

              <div className="mt-1 text-[10px] text-zinc-500">
                received at {new Date(log.timestamp).toLocaleString()}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
