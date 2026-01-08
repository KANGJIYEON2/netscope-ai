from sqlalchemy import Column, String, Float, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, UTC

from db.base import Base
from schemas.enums import SeverityLevel, AnalysisStrategy


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String, primary_key=True)

    summary = Column(String, nullable=False)

    severity = Column(
        SAEnum(SeverityLevel, name="severity_level"),
        nullable=False,
    )

    confidence = Column(Float, nullable=False)

    suspected_causes = Column(JSONB, nullable=False)
    recommended_actions = Column(JSONB, nullable=False)

    matched_rules = Column(JSONB, nullable=False, default=list)

    strategy_used = Column(
        SAEnum(AnalysisStrategy, name="analysis_strategy"),
        nullable=False,
    )

    received_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )