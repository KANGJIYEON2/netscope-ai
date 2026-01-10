"use client";

import { WeeklyReport } from "@/lib/api/report";

const riskColor: Record<string, string> = {
  낮음: "bg-green-500/10 text-green-400 border-green-500/30",
  보통: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
  높음: "bg-red-500/10 text-red-400 border-red-500/30",
  UNKNOWN: "bg-zinc-700 text-zinc-300 border-zinc-600",
};

export default function WeeklyReportCard({ report }: { report: WeeklyReport }) {
  return (
    <section className="rounded-xl border border-zinc-800 bg-zinc-950 p-6 space-y-5">
      <header className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold">📊 주간 운영 리포트</h2>
          <p className="text-xs text-zinc-400">최근 7일간 분석 결과</p>
        </div>

        <span
          className={`
            px-3 py-1 rounded-full text-xs font-bold border
            ${riskColor[report.risk_outlook.level]}
          `}
        >
          다음 주 리스크: {report.risk_outlook.level}
        </span>
      </header>

      <div className="flex gap-6 text-xs text-zinc-400">
        <span>
          기간: {new Date(report.from).toLocaleDateString()} ~{" "}
          {new Date(report.to).toLocaleDateString()}
        </span>
        <span>분석 리포트 수: {report.report_count}</span>
      </div>

      <div className="rounded border border-zinc-800 bg-zinc-900 p-4">
        <pre className="whitespace-pre-wrap text-sm leading-relaxed">
          {report.summary}
        </pre>
      </div>

      <div className="text-sm text-zinc-300">
        <span className="font-semibold">리스크 판단 근거:</span>{" "}
        {report.risk_outlook.reason}
      </div>
    </section>
  );
}
