export type LogLevel = "DEBUG" | "INFO" | "WARN" | "ERROR";

export type LogItem = {
  id: string;
  source: string;
  message: string;
  level: string;
  timestamp: string;
};
