import { LogLevel } from "@/types/log";

const LEVELS: (LogLevel | "ALL")[] = ["ALL", "ERROR", "WARN", "INFO"];

export default function LogFilter({
  value,
  onChange,
}: {
  value: LogLevel | "ALL";
  onChange: (v: LogLevel | "ALL") => void;
}) {
  return (
    <div className="flex gap-2 text-xs">
      {LEVELS.map((l) => (
        <button
          key={l}
          onClick={() => onChange(l)}
          className={`px-2 py-1 rounded border
            ${
              value === l
                ? "bg-emerald-600 text-white border-emerald-500"
                : "border-zinc-700 text-zinc-400"
            }`}
        >
          {l}
        </button>
      ))}
    </div>
  );
}
