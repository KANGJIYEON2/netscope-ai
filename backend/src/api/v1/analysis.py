from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, UTC
import uuid

from src.api.v1.dep import get_current_context
from src.db.session import get_db
from src.model.log import Log
from src.model.analysis_result import AnalysisResult
from src.schemas.analysis import AnalysisRequestDTO, AnalysisResultDTO
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
        summary=analysis.summary,
        severity=analysis.severity,
        confidence=analysis.confidence,
        suspected_causes=analysis.suspected_causes,
        recommended_actions=analysis.recommended_actions,
        matched_rules=analysis.matched_rules,
        strategy_used=analysis.strategy_used,
        received_at=analysis.received_at,
    )
