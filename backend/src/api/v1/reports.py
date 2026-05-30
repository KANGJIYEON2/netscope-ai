from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta, UTC

from src.api.v1.dep import get_current_context
from src.db.session import get_db
from src.model.analysis_result import AnalysisResult
from src.model.weekly_report import WeeklyReport
from src.schemas.analysis import AnalysisResultDTO

import uuid


from src.analysis.gpt_weekly import (
    gpt_explain_weekly,
    gpt_predict_next_week_risk,
)

router = APIRouter(
    prefix="/projects/{project_id}/reports",
    tags=["reports"],
)

# ======================================================
#  분석 리포트 목록 (개별 결과 리스트)
# ======================================================
@router.get("", response_model=list[AnalysisResultDTO])
def list_reports(
    project_id: str,
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
    start_date: date | None = Query(None, description="YYYY-MM-DD"),
    end_date: date | None = Query(None, description="YYYY-MM-DD"),
    limit: int = Query(20, ge=1, le=100),
):
    tenant_id = ctx["tenant_id"]

    q = db.query(AnalysisResult).filter(
        AnalysisResult.tenant_id == tenant_id,
        AnalysisResult.project_id == project_id,
    )

    if start_date:
        q = q.filter(
            AnalysisResult.received_at
            >= datetime.combine(start_date, datetime.min.time())
        )

    if end_date:
        q = q.filter(
            AnalysisResult.received_at
            <= datetime.combine(end_date, datetime.max.time())
        )

    results = (
        q.order_by(AnalysisResult.received_at.desc())
        .limit(limit)
        .all()
    )

    return [
        AnalysisResultDTO(
            id=r.id,
            summary=r.summary,
            severity=r.severity,
            confidence=r.confidence,
            suspected_causes=r.suspected_causes,
            recommended_actions=r.recommended_actions,
            matched_rules=r.matched_rules,
            report_sections=r.report_sections or [],
            investigation_status=r.investigation_status or "open",
            resolution=r.resolution,
            notes=r.notes or [],
            strategy_used=r.strategy_used,
            received_at=r.received_at,
        )
        for r in results
    ]

# ======================================================
# 🔥  주간 운영 리포트 (최근 7일)
# ======================================================
@router.get("/weekly")
def weekly_report(
    project_id: str,
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    tenant_id = ctx["tenant_id"]

    today = datetime.now(UTC).date()
    period_start = today - timedelta(days=7)
    period_end = today

    # ======================================================
    # 1️⃣ 이미 생성된 주간 리포트 있는지 확인
    # ======================================================
    existing = (
        db.query(WeeklyReport)
        .filter(
            WeeklyReport.tenant_id == tenant_id,
            WeeklyReport.project_id == project_id,
            WeeklyReport.period_start == period_start,
            WeeklyReport.period_end == period_end,
        )
        .first()
    )

    if existing:
        return {
            "period": "last_7_days",
            "from": period_start.isoformat(),
            "to": period_end.isoformat(),
            "report_count": existing.report_count,
            "summary": existing.summary,
            "risk_outlook": {
                "level": existing.risk_level,
                "reason": existing.risk_reason,
            },
        }

    # ======================================================
    # 2️⃣ 최근 7일 분석 결과 조회
    # ======================================================
    results = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.tenant_id == tenant_id,
            AnalysisResult.project_id == project_id,
            AnalysisResult.received_at >= datetime.combine(period_start, datetime.min.time()),
        )
        .order_by(AnalysisResult.received_at.desc())
        .all()
    )

    if not results:
        return {
            "period": "last_7_days",
            "from": period_start.isoformat(),
            "to": period_end.isoformat(),
            "report_count": 0,
            "summary": "최근 7일간 분석된 로그가 없습니다.",
            "risk_outlook": {
                "level": "낮음",
                "reason": "분석 대상 로그가 없어 장애 패턴이 감지되지 않았습니다.",
            },
        }

    # ======================================================
    # 3️⃣ 요약 + GPT 분석
    # ======================================================
    rule_summary = "\n".join(
        f"- [{r.severity}] {r.summary}" for r in results
    )

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

    # ======================================================
    # 4️⃣ DB 저장 (🔥 핵심)
    # ======================================================
    weekly = WeeklyReport(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        project_id=project_id,
        period_start=period_start,
        period_end=period_end,
        report_count=len(results),
        summary=weekly_summary,
        risk_level=risk["level"],
        risk_reason=risk["reason"],
    )

    db.add(weekly)
    db.commit()

    return {
        "period": "last_7_days",
        "from": period_start.isoformat(),
        "to": period_end.isoformat(),
        "report_count": weekly.report_count,
        "summary": weekly.summary,
        "risk_outlook": {
            "level": weekly.risk_level,
            "reason": weekly.risk_reason,
        },
    }
# ======================================================
#  분석 리포트 단건 조회
# ======================================================
@router.get("/{analysis_id}", response_model=AnalysisResultDTO)
def get_report(
    project_id: str,
    analysis_id: str,
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    tenant_id = ctx["tenant_id"]

    result = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.id == analysis_id,
            AnalysisResult.tenant_id == tenant_id,
            AnalysisResult.project_id == project_id,
        )
        .first()
    )

    if not result:
        raise HTTPException(status_code=404, detail="Report not found")

    return AnalysisResultDTO(
        id=result.id,
        summary=result.summary,
        severity=result.severity,
        confidence=result.confidence,
        suspected_causes=result.suspected_causes,
        recommended_actions=result.recommended_actions,
        matched_rules=result.matched_rules,
        report_sections=result.report_sections or [],
        investigation_status=result.investigation_status or "open",
        resolution=result.resolution,
        notes=result.notes or [],
        strategy_used=result.strategy_used,
        received_at=result.received_at,
    )


# ======================================================
# Confidence Trend (그래프용)
# ======================================================
@router.get("/trend/confidence")
def confidence_trend(
    project_id: str,
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    tenant_id = ctx["tenant_id"]

    q = db.query(
        func.date(AnalysisResult.received_at).label("day"),
        func.avg(AnalysisResult.confidence).label("avg_confidence"),
        func.count(AnalysisResult.id).label("count"),
    ).filter(
        AnalysisResult.tenant_id == tenant_id,
        AnalysisResult.project_id == project_id,
    )

    if start_date:
        q = q.filter(
            AnalysisResult.received_at
            >= datetime.combine(start_date, datetime.min.time())
        )

    if end_date:
        q = q.filter(
            AnalysisResult.received_at
            <= datetime.combine(end_date, datetime.max.time())
        )

    rows = (
        q.group_by(func.date(AnalysisResult.received_at))
        .order_by(func.date(AnalysisResult.received_at))
        .all()
    )

    return {
        "metric": "confidence_trend",
        "points": [
            {
                "date": row.day,
                "avg_confidence": round(row.avg_confidence, 3),
                "report_count": row.count,
            }
            for row in rows
        ],
    }


