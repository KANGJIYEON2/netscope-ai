import { apiClient } from "@/lib/api/client";

/* ======================
 * Learned Patterns (L1~L4)
 * ====================== */

export type PatternStatus = "candidate" | "labeled" | "promoted" | "dismissed";

export type LearnedPattern = {
  id: string;
  template: string;
  sample: string;
  total_count: number;
  first_seen: string | null;
  last_seen: string | null;
  sources: string[] | null;
  level_dist: Record<string, number> | null;
  hourly_dist: Record<string, number> | null;
  status: PatternStatus;
  label: string | null;
  display_name: string | null;
  causes: string[] | null;
  actions: string[] | null;
  score_seed: number;
  score_adjust: number;
  confirm_count: number;
  dismiss_count: number;
};

export type PatternList = {
  total: number;
  items: LearnedPattern[];
};

export const fetchPatterns = async (params?: {
  status?: PatternStatus;
  limit?: number;
  offset?: number;
}): Promise<PatternList> => {
  const res = await apiClient.get("/patterns", { params });
  return res.data;
};

/* ======================
 * Mutations (L1~L4)
 * ====================== */

export type LabelPatternBody = {
  label: string;
  display_name?: string;
  causes?: string[];
  actions?: string[];
  score_seed?: number;
};

export const labelPattern = async (
  id: string,
  body: LabelPatternBody
): Promise<LearnedPattern> => {
  const res = await apiClient.patch(`/patterns/${id}/label`, body);
  return res.data;
};

export const dismissPattern = async (id: string): Promise<LearnedPattern> => {
  const res = await apiClient.patch(`/patterns/${id}/dismiss`);
  return res.data;
};

export type FeedbackAction = "confirm" | "dismiss" | "wrong";

export const sendPatternFeedback = async (
  id: string,
  action: FeedbackAction
): Promise<unknown> => {
  const res = await apiClient.post(`/patterns/${id}/feedback`, { action });
  return res.data;
};
