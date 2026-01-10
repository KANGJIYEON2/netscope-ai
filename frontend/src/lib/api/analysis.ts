import { apiClient } from "@/lib/api/client";
import { Strategy } from "@/types/analysis";

export const analyzeLogs = async (
  projectId: string,
  logIds: string[],
  strategy: "rule" | "gpt"
) => {
  const res = await apiClient.post(`/projects/${projectId}/analysis`, {
    log_ids: logIds,
    strategy,
  });
  return res.data;
};

export const analyzeTestLogs = async (
  messages: string[],
  strategy: Strategy
) => {
  const res = await apiClient.post("/analysis/test", {
    messages,
    strategy,
  });
  return res.data;
};
