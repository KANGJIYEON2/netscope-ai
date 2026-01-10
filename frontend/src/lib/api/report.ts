import { apiClient } from "@/lib/api/client";

/* ======================
 * Report List
 * ====================== */
export type ReportSummary = {
  summary: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
  confidence: number;
  suspected_causes: string[];
  recommended_actions: string[];
  matched_rules: string[];
  strategy_used: "rule" | "gpt";
  received_at: string;
};

export const fetchReports = async (
  projectId: string,
  params?: {
    start_date?: string;
    end_date?: string;
    limit?: number;
  }
): Promise<ReportSummary[]> => {
  const res = await apiClient.get(`/projects/${projectId}/reports`, { params });
  return res.data;
};

/* ======================
 * Weekly Report
 * ====================== */
export type WeeklyReport = {
  period: string;
  from: string;
  to: string;
  report_count: number;
  summary: string;
  risk_outlook: {
    level: "낮음" | "보통" | "높음" | "UNKNOWN";
    reason: string;
  };
};

export const fetchWeeklyReport = async (
  projectId: string
): Promise<WeeklyReport> => {
  const res = await apiClient.get(`/projects/${projectId}/reports/weekly`);
  return res.data;
};
