import { apiClient } from "@/lib/api/client";
import { LogItem } from "@/types/log";

/* =========================
 * Project List
 * ========================= */

export interface ProjectItem {
  id: string;
  name: string;
  created_at: string;
}

export const fetchProjects = async (): Promise<ProjectItem[]> => {
  const res = await apiClient.get("/projects");
  return res.data;
};

/* =========================
 * Project Create
 * ========================= */

export const createProject = async (name: string): Promise<ProjectItem> => {
  const res = await apiClient.post("/projects", { name });
  return res.data;
};

/* =========================
 * Project Delete
 * ========================= */

export const deleteProject = async (projectId: string) => {
  await apiClient.delete(`/projects/${projectId}`);
};

/* =========================
 * Project Logs
 * ========================= */

export interface ProjectLogsResponse {
  tenant: string;
  project: string;
  count: number;
  logs: LogItem[];
}

export const fetchProjectLogs = async (
  projectId: string,
  limit = 50
): Promise<ProjectLogsResponse> => {
  const res = await apiClient.get(`/projects/${projectId}/logs`, {
    params: { limit },
  });

  return res.data;
};

/* =========================
 * 🔥 Project Overview (Dashboard Card)
 * ========================= */

export interface ProjectOverview {
  project: string;
  current_severity: "LOW" | "MEDIUM" | "HIGH";
  log_count: number;
  error_rate: number;
  last_analysis: {
    at: string;
  } | null;
  top_signals: {
    rule_id: string;
    count: number;
  }[];
}
