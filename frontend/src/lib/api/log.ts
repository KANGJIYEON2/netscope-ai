import { apiClient } from "./client";
import { LogItem } from "@/types/log";

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
): Promise<LogItem> => {
  const res = await apiClient.post<LogItem>(
    `/projects/${projectId}/logs`,
    payload
  );

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
): Promise<LogItem[]> => {
  const res = await apiClient.get<LogItem[]>(`/projects/${projectId}/logs`, {
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
