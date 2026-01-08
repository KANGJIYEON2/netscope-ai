from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, UTC

from db.base import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String, primary_key=True)

    tenant_id = Column(String, nullable=False)
    project_id = Column(String, nullable=False)

    confidence = Column(Float, nullable=False)

    # 🔥 핵심 시그널만 저장
    signals = Column(JSONB, nullable=False)

    received_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )