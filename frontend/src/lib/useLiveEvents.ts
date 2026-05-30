"use client";

import { useEffect, useRef } from "react";
import { API_BASE_URL } from "@/lib/config";

export type LiveEvent = {
  type: "analysis" | "ingest" | string;
  tenant_id: string;
  project_id?: string;
  analysis_id?: string | null;
  severity?: string | null;
  summary?: string | null;
  confidence?: number;
  log_count?: number;
  at?: string;
};

/**
 * Subscribe to the backend SSE stream (cookie-authenticated). Calls `onEvent`
 * for each pushed event. The browser's EventSource auto-reconnects on drop.
 */
export function useLiveEvents(onEvent: (evt: LiveEvent) => void) {
  const cb = useRef(onEvent);
  useEffect(() => {
    cb.current = onEvent;
  });

  useEffect(() => {
    const es = new EventSource(`${API_BASE_URL}/events/stream`, {
      withCredentials: true,
    });

    es.onmessage = (e) => {
      try {
        cb.current(JSON.parse(e.data) as LiveEvent);
      } catch {
        /* ignore non-JSON heartbeats */
      }
    };

    // EventSource reconnects automatically; swallow transient errors.
    es.onerror = () => {};

    return () => es.close();
  }, []);
}
