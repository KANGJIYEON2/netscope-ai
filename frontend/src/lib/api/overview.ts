import { apiClient } from "@/lib/api/client";

export type ProjectOverview = {
  log_count_24h: number;
  error_rate: number;
  last_analysis?: {
    confidence: number;
    severity: string;
    created_at: string;
  };
};

export const fetchProjectOverview = async (): Promise<ProjectOverview> => {
  const res = await apiClient.get("/projects/overview");
  return res.data;
};
