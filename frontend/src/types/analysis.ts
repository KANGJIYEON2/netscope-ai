export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type Strategy = "rule" | "gpt" | "ai" | "hybrid";

/** GPT 보고서 본문 한 섹션 (summary 다음의 상세 설명). */
export interface ReportSection {
  title: string;
  body: string;
}

export type InvestigationStatus =
  | "open"
  | "investigating"
  | "resolved"
  | "false_positive";

export interface InvestigationNote {
  at: string;
  text: string;
}

export interface AnalysisResult {
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
}
