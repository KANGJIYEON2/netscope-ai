# analysis/weekly_service.py

from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import Session
import uuid

from src.model.analysis_result import AnalysisResult
from src.model.weekly_report import WeeklyReport
from src.analysis.gpt_weekly import (
    gpt_explain_weekly,
    gpt_predict_next_week_risk,
)

# ===== MVP 기준 정책 =====
MIN_ANALYSIS_COUNT = 5  # 최근 7일 최소 분석 개수


def should_generate_weekly_report(
    db: Session,
    tenant_id: str,
    project_id: str,
) -> bool:
    """
    주간 리포트 생성 조건 판단
    - 최근 7일 AnalysisResult >= MIN_ANALYSIS_COUNT
    - 동일 기간 주간 리포트가 아직 없음
    """
    now = datetime.now(UTC)
    since = now - timedelta(days=7)

    analysis_count = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.tenant_id == tenant_id,
            AnalysisResult.project_id == project_id,
            AnalysisResult.received_at >= since,
        )
        .count()
    )

    if analysis_count < MIN_ANALYSIS_COUNT:
        return False

    exists = (
        db.query(WeeklyReport)
        .filter(
            WeeklyReport.tenant_id == tenant_id,
            WeeklyReport.project_id == project_id,
            WeeklyReport.period_start == since.date(),
        )
        .first()
    )

    return exists is None


def generate_and_save_weekly_report(
    db: Session,
    tenant_id: str,
    project_id: str,
) -> WeeklyReport:
    """
    최근 7일 AnalysisResult 기반으로
    - GPT 주간 요약
    - 다음 주 리스크 판단
    - WeeklyReport DB 저장
    """
    now = datetime.now(UTC)
    since = now - timedelta(days=7)

    results = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.tenant_id == tenant_id,
            AnalysisResult.project_id == project_id,
            AnalysisResult.received_at >= since,
        )
        .order_by(AnalysisResult.received_at.desc())
        .all()
    )

    if not results:
        raise ValueError("No analysis results for weekly report")

    # Rule summary
    rule_summary = "\n".join(
        f"- [{r.severity}] {r.summary}"
        for r in results
        if r.summary
    )

    # signals 병합
    signals = []
    for r in results:
        if r.signals:
            signals.extend(r.signals)

    weekly_summary = gpt_explain_weekly(
        rule_summary=rule_summary,
        signals=signals,
    )

    risk = gpt_predict_next_week_risk(
        rule_summary=rule_summary,
        signals=signals,
    )

    report = WeeklyReport(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        project_id=project_id,
        period_start=since.date(),
        period_end=now.date(),
        report_count=len(results),
        summary=weekly_summary,
        risk_level=risk["level"],
        risk_reason=risk["reason"],
        created_at=now,
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return report
