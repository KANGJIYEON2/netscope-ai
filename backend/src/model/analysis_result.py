from sqlalchemy import Column, String, Float, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, UTC

from db.base import Base
from schemas.enums import SeverityLevel


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String, primary_key=True)

    # 🔥 멀티테넌시 / 프로젝트 단위
    tenant_id = Column(String, nullable=False, index=True)
    project_id = Column(String, nullable=False, index=True)

    # 🔥 리포트 핵심 요약
    summary = Column(Text, nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=False)
    confidence = Column(Float, nullable=False)

    # 🔥 리포트 상세 본문
    suspected_causes = Column(JSONB, nullable=False)
    recommended_actions = Column(JSONB, nullable=False)
    matched_rules = Column(JSONB, nullable=False, default=list)

    # 🔥 Rule Engine 결과 (weekly용)
    signals = Column(JSONB, nullable=False)

    # 🔥 분석 방식
    strategy_used = Column(String, nullable=False)

    # 🔥 분석 수행 시각
    received_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
