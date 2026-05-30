from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, UTC
import uuid

from src.api.v1.dep import get_current_context
from src.db.session import get_db
from src.model.log import Log
from src.model.analysis_result import AnalysisResult
from src.schemas.analysis import (
    AnalysisRequestDTO,
    AnalysisResultDTO,
    InvestigationUpdateDTO,
    NoteCreateDTO,
)
from src.analysis.engine import AnalysisEngine
from src.analysis.weekly_service import (
    should_generate_weekly_report,
    generate_and_save_weekly_report,
)

router = APIRouter(
    prefix="/projects/{project_id}/analysis",
    tags=["analysis"],
)

engine = AnalysisEngine()


# ======================================================
# 1️⃣ 로그 묶음 분석 실행 (POST)
# ======================================================
@router.post(
    "",
    response_model=AnalysisResultDTO,
    status_code=status.HTTP_201_CREATED,
)
def analyze_logs(
    project_id: str,
    dto: AnalysisRequestDTO,
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    tenant_id = ctx["tenant_id"]

    # 1️⃣ 로그 조회 (보안 경계 강제)
    logs = (
        db.query(Log)
        .filter(
            Log.id.in_(dto.log_ids),
            Log.tenant_id == tenant_id,
            Log.project_id == project_id,
        )
        .all()
    )

    if len(logs) != len(dto.log_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some log_ids are invalid or not accessible",
        )

    # 2️⃣ 분석 실행
    result = engine.analyze(logs, dto.strategy)

    # 2.5️⃣ 패턴 매칭 (L2 — learned patterns)
    matched_patterns = []
    try:
        from src.learning.matcher import match_patterns
        matched_patterns = match_patterns(
            db=db,
            tenant_id=tenant_id,
            messages=[log.message for log in logs],
        )
        # Add pattern scores to confidence
        pattern_score = sum(p["score"] for p in matched_patterns)
        if pattern_score > 0:
            result["confidence"] = min(result["confidence"] + pattern_score, 1.0)
    except Exception:
        pass  # Pattern matching failure must not break analysis
    """
    result 예시:
    {
        "summary": str,
        "severity": SeverityLevel,
        "confidence": float,
        "signals": list[dict],
        "suspected_causes": list[str],
        "recommended_actions": list[str],
        "matched_rules": list[str],
        "strategy_used": str,
    }
    """

    # 3️⃣ 분석 결과 저장
    analysis = AnalysisResult(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        project_id=project_id,
        summary=result["summary"],
        severity=result["severity"],
        confidence=result["confidence"],
        signals=result["signals"],
        suspected_causes=result["suspected_causes"],
        recommended_actions=result["recommended_actions"],
        matched_rules=result.get("matched_rules", []),
        report_sections=result.get("report_sections", []),
        strategy_used=result.get("strategy_used", dto.strategy),
        received_at=datetime.now(UTC),
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # 🔥 4️⃣ 주간 리포트 자동 생성 트리거 (MVP 핵심)
    if should_generate_weekly_report(db, tenant_id, project_id):
        generate_and_save_weekly_report(
            db=db,
            tenant_id=tenant_id,
            project_id=project_id,
        )

    # 5️⃣ 응답
    return AnalysisResultDTO(
        id=analysis.id,
        summary=analysis.summary,
        severity=analysis.severity,
        confidence=analysis.confidence,
        suspected_causes=analysis.suspected_causes,
        recommended_actions=analysis.recommended_actions,
        matched_rules=analysis.matched_rules,
        report_sections=analysis.report_sections or [],
        investigation_status=analysis.investigation_status or "open",
        resolution=analysis.resolution,
        notes=analysis.notes or [],
        matched_patterns=matched_patterns,
        strategy_used=analysis.strategy_used,
        received_at=analysis.received_at,
    )


# ======================================================
# 2️⃣ 조사 & 해결 (Investigation) — 사후 기록 + 학습
# ======================================================
def _get_analysis_or_404(db, tenant_id, project_id, analysis_id) -> AnalysisResult:
    row = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.id == analysis_id,
            AnalysisResult.tenant_id == tenant_id,
            AnalysisResult.project_id == project_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return row


_VALID_STATUS = {"open", "investigating", "resolved", "false_positive"}


@router.patch("/{analysis_id}/investigation")
def update_investigation(
    project_id: str,
    analysis_id: str,
    dto: InvestigationUpdateDTO,
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    """조사 상태 / 실제 원인(resolution) 갱신."""
    row = _get_analysis_or_404(db, ctx["tenant_id"], project_id, analysis_id)

    if dto.status is not None:
        if dto.status not in _VALID_STATUS:
            raise HTTPException(status_code=400, detail="invalid status")
        row.investigation_status = dto.status
    if dto.resolution is not None:
        row.resolution = dto.resolution.strip() or None

    db.commit()
    db.refresh(row)
    return {
        "id": row.id,
        "investigation_status": row.investigation_status,
        "resolution": row.resolution,
        "notes": row.notes or [],
    }


@router.post("/{analysis_id}/notes")
def add_note(
    project_id: str,
    analysis_id: str,
    dto: NoteCreateDTO,
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    """메모 타임라인에 한 줄 추가 (append-only)."""
    row = _get_analysis_or_404(db, ctx["tenant_id"], project_id, analysis_id)

    note = {"at": datetime.now(UTC).isoformat(), "text": dto.text.strip()}
    # JSONB 리스트는 새 리스트로 재할당해야 SQLAlchemy가 변경을 감지함
    row.notes = list(row.notes or []) + [note]

    db.commit()
    return {"id": row.id, "notes": row.notes}


@router.get("/{analysis_id}/similar")
def similar_resolved(
    project_id: str,
    analysis_id: str,
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    """
    학습: 같은 룰 조합으로 '해결됨(resolved)' 처리된 과거 분석의 실제 원인을 추천.
    matched_rules 교집합이 큰 순으로 정렬.
    """
    tenant_id = ctx["tenant_id"]
    base = _get_analysis_or_404(db, tenant_id, project_id, analysis_id)
    base_rules = set(base.matched_rules or [])
    if not base_rules:
        return {"items": []}

    resolved = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.tenant_id == tenant_id,
            AnalysisResult.investigation_status == "resolved",
            AnalysisResult.resolution.isnot(None),
            AnalysisResult.id != analysis_id,
        )
        .order_by(AnalysisResult.received_at.desc())
        .limit(200)
        .all()
    )

    scored = []
    for r in resolved:
        overlap = base_rules & set(r.matched_rules or [])
        if not overlap:
            continue
        scored.append({
            "id": r.id,
            "project_id": r.project_id,
            "summary": r.summary,
            "resolution": r.resolution,
            "severity": r.severity,
            "matched_rules": list(overlap),
            "overlap": len(overlap),
            "received_at": r.received_at.isoformat(),
        })

    scored.sort(key=lambda x: x["overlap"], reverse=True)
    return {"items": scored[:5]}
