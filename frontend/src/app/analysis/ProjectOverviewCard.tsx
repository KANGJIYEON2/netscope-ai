import SeverityBadge from "./SeverityBadge";
import { ProjectOverview } from "@/lib/api/project";

type Props = {
  data: ProjectOverview;
  onViewReport: () => void;
};

export default function ProjectOverviewCard({ data, onViewReport }: Props) {
  return (
    <div className="border rounded-lg p-6 bg-white shadow-sm space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">Project: {data.project}</h2>
        <SeverityBadge severity={data.current_severity} />
      </div>

      <div className="grid grid-cols-3 gap-4 text-sm">
        <div>
          <p className="text-gray-500">Logs (24h)</p>
          <p className="font-semibold">{data.log_count}</p>
        </div>

        <div>
          <p className="text-gray-500">Error Rate</p>
          <p className="font-semibold">{(data.error_rate * 100).toFixed(1)}%</p>
        </div>

        <div>
          <p className="text-gray-500">Last Analysis</p>
          <p className="font-semibold">
            {data.last_analysis
              ? new Date(data.last_analysis.at).toLocaleString()
              : "N/A"}
          </p>
        </div>
      </div>

      <div>
        <p className="text-gray-500 text-sm mb-2">Top Signals</p>
        <ul className="flex gap-2 flex-wrap">
          {data.top_signals.map((s) => (
            <li
              key={s.rule_id}
              className="px-2 py-1 bg-gray-100 rounded text-sm"
            >
              {s.rule_id} × {s.count}
            </li>
          ))}
        </ul>
      </div>

      <div className="text-right">
        <button
          onClick={onViewReport}
          className="px-4 py-2 bg-black text-white rounded"
        >
          분석 보기 →
        </button>
      </div>
    </div>
  );
}
