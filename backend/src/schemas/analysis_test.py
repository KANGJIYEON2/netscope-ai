from pydantic import BaseModel, Field
from typing import List

from .enums import AnalysisStrategy


class TestAnalysisRequestDTO(BaseModel):
    messages: List[str] = Field(..., min_items=1)
    strategy: AnalysisStrategy = Field(default=AnalysisStrategy.RULE)
