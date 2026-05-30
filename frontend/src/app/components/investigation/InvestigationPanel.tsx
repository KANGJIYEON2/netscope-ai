"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  ClipboardCheck,
  Lightbulb,
  MessageSquarePlus,
  Sparkles,
  Send,
} from "lucide-react";

import type {
  InvestigationStatus,
  InvestigationNote,
} from "@/types/analysis";
import type { ReportSummary } from "@/lib/api/report";
import {
  updateInvestigation,
  addInvestigationNote,
  fetchSimilarResolved,
  type SimilarCase,
} from "@/lib/api/investigation";
import { timeAgo } from "@/lib/time";

const STATUSES: { key: InvestigationStatus; label: string; cls: string }[] = [
  { key: "open", label: "열림", cls: "bg-zinc-700/50 text-zinc-300" },
  { key: "investigating", label: "조사중", cls: "bg-amber-500/20 text-amber-300" },
  { key: "resolved", label: "해결됨", cls: "bg-emerald-500/20 text-emerald-300" },
  { key: "false_positive", label: "오탐", cls: "bg-rose-500/20 text-rose-300" },
];

/**
 * 조사 & 해결 패널 — 분석 보고서별 사후 기록 + 학습 추천.
 * - 상태(열림/조사중/해결됨/오탐)
 * - 실제 원인(resolution)
 * - 메모 타임라인
 * - 📌 같은 룰 조합으로 과거 '해결됨' 된 사례의 실제 원인 추천
 */
export function InvestigationPanel({
  projectId,
  report,
}: {
  projectId: string;
  report: ReportSummary;
}) {
  const analysisId = report.id;

  const [status, setStatus] = useState<InvestigationStatus>(
    report.investigation_status ?? "open"
  );
  const [resolution, setResolution] = useState(report.resolution ?? "");
  const [notes, setNotes] = useState<InvestigationNote[]>(report.notes ?? []);
  const [noteText, setNoteText] = useState("");
  const [similar, setSimilar] = useState<SimilarCase[]>([]);
  const [busy, setBusy] = useState(false);
  const [savedTick, setSavedTick] = useState(false);

  useEffect(() => {
    if (!analysisId) return;
    fetchSimilarResolved(projectId, analysisId)
      .then(setSimilar)
      .catch(() => setSimilar([]));
  }, [projectId, analysisId]);

  if (!analysisId) return null;

  const setStatusAndSave = async (next: InvestigationStatus) => {
    setStatus(next);
    setBusy(true);
    try {
      await updateInvestigation(projectId, analysisId, { status: next });
    } finally {
      setBusy(false);
    }
  };

  const saveResolution = async () => {
    setBusy(true);
    try {
      await updateInvestigation(projectId, analysisId, { resolution });
      setSavedTick(true);
      setTimeout(() => setSavedTick(false), 1500);
    } finally {
      setBusy(false);
    }
  };

  const submitNote = async () => {
    if (!noteText.trim()) return;
    setBusy(true);
    try {
      const res = await addInvestigationNote(projectId, analysisId, noteText.trim());
      setNotes(res.notes);
      setNoteText("");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4 rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
      <div className="flex items-center gap-2">
        <ClipboardCheck size={15} className="text-cyan-400" />
        <h4 className="text-xs font-semibold text-zinc-200">조사 &amp; 해결</h4>
      </div>

      {/* status pills */}
      <div className="flex flex-wrap gap-1.5">
        {STATUSES.map((s) => (
          <button
            key={s.key}
            disabled={busy}
            onClick={() => setStatusAndSave(s.key)}
            className={
              "rounded-full px-2.5 py-1 text-[11px] font-semibold transition " +
              (status === s.key
                ? s.cls + " ring-1 ring-inset ring-white/20"
                : "bg-zinc-800/60 text-zinc-500 hover:text-zinc-300")
            }
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* real root cause */}
      <div>
        <label className="mb-1 flex items-center gap-1.5 text-[11px] font-medium text-zinc-400">
          <Lightbulb size={12} className="text-amber-400" /> 실제 원인 (root cause)
        </label>
        <div className="flex gap-2">
          <textarea
            value={resolution}
            onChange={(e) => setResolution(e.target.value)}
            placeholder="예) 확인해보니 프론트엔드 nginx rewrite 경로 설정 오류였음"
            rows={2}
            className="flex-1 resize-none rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs text-zinc-200 outline-none focus:border-cyan-600"
          />
          <button
            onClick={saveResolution}
            disabled={busy}
            className="shrink-0 self-start rounded-lg bg-zinc-800 px-3 py-2 text-xs font-medium text-zinc-200 hover:bg-zinc-700 disabled:opacity-50"
          >
            {savedTick ? "저장됨 ✓" : "저장"}
          </button>
        </div>
      </div>

      {/* notes timeline */}
      <div>
        <label className="mb-1 flex items-center gap-1.5 text-[11px] font-medium text-zinc-400">
          <MessageSquarePlus size={12} className="text-sky-400" /> 조사 메모
        </label>
        {notes.length > 0 && (
          <ul className="mb-2 space-y-1.5 border-l border-zinc-800 pl-3">
            {notes.map((n, i) => (
              <motion.li
                key={i}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                className="relative text-xs text-zinc-300"
              >
                <span className="absolute -left-[14px] top-1.5 h-1.5 w-1.5 rounded-full bg-sky-400" />
                <span className="text-[10px] text-zinc-600">{timeAgo(n.at)}</span>{" "}
                {n.text}
              </motion.li>
            ))}
          </ul>
        )}
        <div className="flex gap-2">
          <input
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submitNote()}
            placeholder="조사 현황 한 줄 기록…"
            className="flex-1 rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-200 outline-none focus:border-cyan-600"
          />
          <button
            onClick={submitNote}
            disabled={busy}
            className="flex items-center gap-1 rounded-lg bg-zinc-800 px-3 py-1.5 text-xs text-zinc-200 hover:bg-zinc-700 disabled:opacity-50"
          >
            <Send size={12} />
          </button>
        </div>
      </div>

      {/* learned similar cases */}
      {similar.length > 0 && (
        <div className="rounded-lg border border-violet-900/40 bg-violet-500/5 p-3">
          <p className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold text-violet-300">
            <Sparkles size={12} /> 과거 유사 해결 사례 · 학습 추천
          </p>
          <ul className="space-y-2">
            {similar.map((c) => (
              <li key={c.id} className="text-xs">
                <p className="text-zinc-300">
                  <span className="font-semibold text-emerald-300">→ {c.resolution}</span>
                </p>
                <p className="mt-0.5 text-[10px] text-zinc-500">
                  {c.summary} · 룰 {c.overlap}개 일치 ({c.matched_rules
                    .map((r) => r.match(/^R\d+/)?.[0] ?? r)
                    .join(", ")})
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
