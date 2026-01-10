import { apiClient } from "@/lib/api/client";
import { Log } from "@/types/log";

/* =========================
 * Project List
 * ========================= */

export interface ProjectItem {
  id: string;
  name: string;
  created_at: string;
}

export const fetchProjects = async (): Promise<ProjectItem[]> => {
  const res = await apiClient.get("/projects"); // ✅ 여기 중요
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
  logs: Log[];
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
