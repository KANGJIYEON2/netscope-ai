from fastapi import APIRouter, Header
from datetime import datetime, timedelta

from db.session import SessionLocal
from model.analysis_result import AnalysisResult

from analysis.rule_engine import confidence_level
from analysis.rule_summary import build_rule_summary
from analysis.gpt_weekly import (
    gpt_explain_weekly,
    gpt_risk_outlook,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/weekly")
def weekly_report(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_project_id: str = Header(..., alias="X-Project-ID"),
):
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(days=7)

        results = (
            db.query(AnalysisResult)
            .filter(
                AnalysisResult.tenant_id == x_tenant_id,
                AnalysisResult.project_id == x_project_id,
                AnalysisResult.received_at >= since,
            )
            .order_by(AnalysisResult.received_at.desc())
            .all()
        )

        # 🔹 signals 집계 (룰 엔진 증거)
        all_signals = []
        for r in results:
            all_signals.extend(r.signals or [])

        # 🔹 룰 기반 사실 요약 (deterministic / 저장 가능 레벨)
        rule_summary = build_rule_summary(all_signals)

        # 🔹 GPT 기반 주간 보고서 (응답 전용)
        report = gpt_explain_weekly(
            rule_summary=rule_summary,
            signals=all_signals,
        )

        # 🔹 GPT 기반 다음 주 리스크 전망 (응답 전용)
        risk_outlook = gpt_risk_outlook(
            rule_summary=rule_summary,
            signals=all_signals,
        )

        return {
            "tenant": x_tenant_id,
            "project": x_project_id,
            "period": "last_7_days",
            "count": len(results),

            # 👇 핵심 결과
            "rule_summary": rule_summary,
            "report": report,
            "risk_outlook": risk_outlook,

            # 👇 raw evidence
            "reports": [
                {
                    "confidence": r.confidence,
                    "severity": confidence_level(r.confidence),
                    "signals": r.signals,
                    "created_at": r.received_at,
                }
                for r in results
            ],
        }

    finally:
        db.close()
