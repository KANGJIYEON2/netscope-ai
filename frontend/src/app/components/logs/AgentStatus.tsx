"use client";

interface AgentStatusProps {
  connected: boolean;
  lastSeen?: string;
}

export default function AgentStatus({ connected, lastSeen }: AgentStatusProps) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span
        className={`h-2 w-2 rounded-full ${
          connected ? "bg-emerald-400" : "bg-red-500"
        }`}
      />
      <span className="text-zinc-400">
        Agent {connected ? "connected" : "disconnected"}
      </span>

      {lastSeen && <span className="text-zinc-500">· last log {lastSeen}</span>}
    </div>
  );
}
