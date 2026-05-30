import { apiClient } from "@/lib/api/client";
import type {
  Severity,
  Strategy,
  ReportSection,
  InvestigationStatus,
  InvestigationNote,
} from "@/types/analysis";

/* ======================
 * Report List
 * ====================== */
export type ReportSummary = {
  id?: string;
  summary: string;
  severity: Severity;
  confidence: number;
  suspected_causes: string[];
  recommended_actions: string[];
  matched_rules: string[];
  report_sections?: ReportSection[];
  investigation_status?: InvestigationStatus;
  resolution?: string | null;
  notes?: InvestigationNote[];
  strategy_used: Strategy;
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

/* ======================
 * Confidence Trend (그래프용)
 * ====================== */
export type TrendPoint = {
  date: string; // YYYY-MM-DD
  avg_confidence: number;
  report_count: number;
};

export type ConfidenceTrend = {
  metric: string;
  points: TrendPoint[];
};

export const fetchConfidenceTrend = async (
  projectId: string,
  params?: { start_date?: string; end_date?: string }
): Promise<ConfidenceTrend> => {
  const res = await apiClient.get(
    `/projects/${projectId}/reports/trend/confidence`,
    { params }
  );
  return res.data;
};

/** Confidence 임계선 (대시보드 트렌드 차트 공용) */
export const CONFIDENCE_THRESHOLDS = { warn: 0.45, high: 0.75 } as const;
