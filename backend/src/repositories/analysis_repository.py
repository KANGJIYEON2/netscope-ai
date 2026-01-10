from sqlalchemy.orm import Session
from src.model.analysis_result import AnalysisResult
from src.schemas.analysis import AnalysisResultDTO


def save_analysis_result(
    db: Session,
    dto: AnalysisResultDTO,
) -> AnalysisResult:
    """
    DTO → ORM Model → DB 저장
    """

    model = AnalysisResult(
        summary=dto.summary,
        severity=dto.severity,
        confidence=dto.confidence,
        suspected_causes=dto.suspected_causes,
        recommended_actions=dto.recommended_actions,
        matched_rules=dto.matched_rules,
        strategy_used=dto.strategy_used,
        received_at=dto.received_at,
    )

    db.add(model)
    db.commit()
    db.refresh(model)

    return model
