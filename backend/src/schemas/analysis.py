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


class AnalysisResultDTO(BaseModel):
    """
    분석 결과 응답 DTO
    """
    summary: str
    severity: SeverityLevel
    confidence: float = Field(ge=0.0, le=1.0)

    suspected_causes: List[str] = Field(min_items=1)
    recommended_actions: List[str] = Field(min_items=1)

    # 왜 이렇게 판단됐는지
    matched_rules: List[str] = Field(default_factory=list)

    # 실제 사용된 전략
    strategy_used: str = Field(default="rule")

    # 서버 수신 시각
    received_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
