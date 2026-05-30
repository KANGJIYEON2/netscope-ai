from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, UTC

from .enums import AnalysisStrategy, SeverityLevel


class AnalysisRequestDTO(BaseModel):
    """
    로그 묶음 분석 요청 DTO
    """
    log_ids: List[str] = Field(
        ...,
        min_items=1,
        description="분석 대상 로그 ID 목록",
    )
    strategy: AnalysisStrategy = Field(
        default=AnalysisStrategy.RULE,
        description="분석 전략 (rule / gpt)",
    )


class InvestigationNote(BaseModel):
    at: str
    text: str


class InvestigationUpdateDTO(BaseModel):
    """조사 상태 / 실제 원인 갱신 요청."""
    status: str | None = None  # open | investigating | resolved | false_positive
    resolution: str | None = None


class NoteCreateDTO(BaseModel):
    text: str = Field(min_length=1)


class AnalysisResultDTO(BaseModel):
    """
    분석 결과 응답 DTO
    """
    # 분석 식별자 (조사/메모 기능이 특정 분석을 가리키기 위해 필요)
    id: str | None = None

    summary: str
    severity: SeverityLevel
    confidence: float = Field(ge=0.0, le=1.0)

    suspected_causes: List[str] = Field(min_items=1)
    recommended_actions: List[str] = Field(min_items=1)

    # 왜 이렇게 판단됐는지
    matched_rules: List[str] = Field(default_factory=list)

    # GPT 보고서 본문 [{title, body}] — 상단 summary 다음의 상세 설명
    report_sections: List[dict] = Field(default_factory=list)

    # 조사 & 해결 (Investigation)
    investigation_status: str = Field(default="open")
    resolution: str | None = None
    notes: List[dict] = Field(default_factory=list)

    # 학습된 패턴 매칭 (L2)
    matched_patterns: List[dict] = Field(default_factory=list)

    # 실제 사용된 전략
    strategy_used: str = Field(default="rule")

    # 서버 수신 시각
    received_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
