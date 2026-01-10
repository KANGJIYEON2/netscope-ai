import { apiClient } from "./client";
import { Log } from "@/types/log";

/* =========================
 * Log Create (Manual / Incoming 공용)
 * POST /projects/{projectId}/logs
 * ========================= */

export type CreateLogPayload = {
  source: string;
  message: string;
  level: "INFO" | "WARN" | "ERROR";
  timestamp?: string; // 서버 default 사용 가능
};

export const createLog = async (
  projectId: string,
  payload: CreateLogPayload
): Promise<Log> => {
  const res = await apiClient.post<Log>(`/projects/${projectId}/logs`, payload);

  return res.data;
};

/* =========================
 * Log List
 * GET /projects/{projectId}/logs
 * ========================= */

export const fetchLogs = async (
  projectId: string,
  params?: {
    limit?: number;
  }
): Promise<Log[]> => {
  const res = await apiClient.get<Log[]>(`/projects/${projectId}/logs`, {
    params,
  });

  return res.data;
};

/* =========================
 * Log Delete
 * DELETE /projects/{projectId}/logs/{logId}
 * ========================= */

export const deleteLog = async (
  projectId: string,
  logId: string
): Promise<void> => {
  await apiClient.delete(`/projects/${projectId}/logs/${logId}`);
};
