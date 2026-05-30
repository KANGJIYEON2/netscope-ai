import { apiClient } from "@/lib/api/client";
import type {
  InvestigationStatus,
  InvestigationNote,
  Severity,
} from "@/types/analysis";

/* ======================
 * Investigation & Resolution (조사 / 해결 / 학습)
 * ====================== */

export const updateInvestigation = async (
  projectId: string,
  analysisId: string,
  body: { status?: InvestigationStatus; resolution?: string }
): Promise<{
  id: string;
  investigation_status: InvestigationStatus;
  resolution: string | null;
  notes: InvestigationNote[];
}> => {
  const res = await apiClient.patch(
    `/projects/${projectId}/analysis/${analysisId}/investigation`,
    body
  );
  return res.data;
};

export const addInvestigationNote = async (
  projectId: string,
  analysisId: string,
  text: string
): Promise<{ id: string; notes: InvestigationNote[] }> => {
  const res = await apiClient.post(
    `/projects/${projectId}/analysis/${analysisId}/notes`,
    { text }
  );
  return res.data;
};

export type SimilarCase = {
  id: string;
  project_id: string;
  summary: string;
  resolution: string;
  severity: Severity;
  matched_rules: string[];
  overlap: number;
  received_at: string;
};

export const fetchSimilarResolved = async (
  projectId: string,
  analysisId: string
): Promise<SimilarCase[]> => {
  const res = await apiClient.get(
    `/projects/${projectId}/analysis/${analysisId}/similar`
  );
  return res.data.items ?? [];
};
