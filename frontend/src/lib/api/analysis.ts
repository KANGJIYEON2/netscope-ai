import axios from "axios";
import { API_BASE_URL } from "../config";
import { Strategy } from "@/types/analysis";

export const analyzeLogs = async (logIds: string[], strategy: Strategy) => {
  const res = await axios.post(`${API_BASE_URL}/analysis`, {
    log_ids: logIds,
    strategy,
  });
  return res.data;
};
