from sqlalchemy import Column, String, Float, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, UTC

from src.db.base import Base
from src.schemas.enums import SeverityLevel


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

    # 🔥 GPT 보고서 본문 [{title, body}] — summary 다음의 상세 설명 (rule-only면 빈 배열)
    report_sections = Column(JSONB, nullable=True, default=list)

    # 🔥 조사 & 해결 (Investigation) — 사람이 기록하는 사후 조사 현황/학습
    #    status: open | investigating | resolved | false_positive
    #    resolution: 실제 규명된 원인 (예: "프론트 경로 설정 오류")
    #    notes: 메모 타임라인 [{at, text}]
    investigation_status = Column(String, nullable=True, default="open")
    resolution = Column(Text, nullable=True)
    notes = Column(JSONB, nullable=True, default=list)

    # 🔥 분석 방식
    strategy_used = Column(String, nullable=False)

    # 🔥 분석 수행 시각
    received_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
