import axios from "axios";
import { API_BASE_URL } from "../config";
import { Log } from "@/types/log";

export const createLog = async (payload: {
  source: string;
  message: string;
  level: string;
  timestamp: string;
}) => {
  const res = await axios.post(`${API_BASE_URL}/logs`, payload);
  return res.data;
};

export const fetchLogs = async (): Promise<Log[]> => {
  const res = await axios.get(`${API_BASE_URL}/logs`);
  return res.data;
};
