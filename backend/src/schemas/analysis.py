from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, UTC

from .enums import AnalysisStrategy, SeverityLevel


class AnalysisRequestDTO(BaseModel):
    log_ids: List[str] = Field(..., min_items=1)
    strategy: AnalysisStrategy = Field(default=AnalysisStrategy.RULE)


class AnalysisResultDTO(BaseModel):
    summary: str
    severity: SeverityLevel
    confidence: float = Field(ge=0.0, le=1.0)

    suspected_causes: List[str] = Field(min_items=1)
    recommended_actions: List[str] = Field(min_items=1)

    # ✅ “왜 이렇게 나왔는지” 바로 확인
    matched_rules: List[str] = Field(default_factory=list)

    # ✅ rule / gpt / rule_fallback
    strategy_used: str = Field(default="rule")

    # (선택) 서버 시각
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
