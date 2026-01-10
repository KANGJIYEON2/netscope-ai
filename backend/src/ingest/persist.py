from uuid import uuid4
from datetime import datetime, UTC

from src.db.session import SessionLocal
from src.model.analysis_result import AnalysisResult


def persist_analysis(*, tenant_id: str, project_id: str, aggregated: dict):
    db = SessionLocal()
    try:
        result = AnalysisResult(
            id=str(uuid4()),
            tenant_id=tenant_id,
            project_id=project_id,
            confidence=aggregated["confidence"],
            signals=aggregated["signals"],
            received_at=datetime.now(UTC),
        )

        db.add(result)
        db.commit()
    finally:
        db.close()