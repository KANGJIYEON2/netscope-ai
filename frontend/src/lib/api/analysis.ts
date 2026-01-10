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
