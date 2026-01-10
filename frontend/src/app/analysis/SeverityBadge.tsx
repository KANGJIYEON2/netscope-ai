type Props = {
  severity: "LOW" | "MEDIUM" | "HIGH" | "UNKNOWN";
};

const colorMap = {
  LOW: "bg-green-500",
  MEDIUM: "bg-yellow-500",
  HIGH: "bg-red-500",
  UNKNOWN: "bg-gray-400",
};

export default function SeverityBadge({ severity }: Props) {
  return (
    <span
      className={`px-3 py-1 rounded text-sm font-semibold text-white ${colorMap[severity]}`}
    >
      {severity}
    </span>
  );
}
