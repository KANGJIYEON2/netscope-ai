export type LogLevel = "DEBUG" | "INFO" | "WARN" | "ERROR";

export interface Log {
  id: string;
  source: string;
  message: string;
  level: LogLevel;
  timestamp: string;
  received_at: string;
}
