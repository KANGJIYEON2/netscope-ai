export type Severity = "LOW" | "MEDIUM" | "HIGH";
export type Strategy = "rule" | "gpt";

export interface AnalysisResult {
  summary: string;
  severity: Severity;
  confidence: number;
  suspected_causes: string[];
  recommended_actions: string[];
  matched_rules: string[];
  strategy_used: Strategy;
  received_at: string;
}
