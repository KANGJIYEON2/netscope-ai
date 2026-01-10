export default function SeverityBadge({
  level,
}: {
  level: "LOW" | "MEDIUM" | "HIGH" | "UNKNOWN";
}) {
  const color =
    level === "HIGH"
      ? "bg-red-600"
      : level === "MEDIUM"
      ? "bg-yellow-500"
      : level === "LOW"
      ? "bg-emerald-600"
      : "bg-zinc-600";

  return (
    <span className={`px-2 py-1 rounded text-xs text-white ${color}`}>
      {level}
    </span>
  );
}
