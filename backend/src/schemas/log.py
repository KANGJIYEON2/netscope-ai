from pydantic import BaseModel, Field
from datetime import datetime, UTC
from typing import Optional
from src.schemas.enums import LogLevel


class LogCreateDTO(BaseModel):
    """
    수동 로그 입력 / ingest 공용
    """
    source: str = Field(
        ...,
        min_length=2,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        description="로그 발생 소스",
    )

    message: str = Field(
        ...,
        min_length=1,
        description="로그 메시지",
    )

    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="로그 레벨",
    )

    timestamp: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(UTC),
        description="로그 발생 시각 (UTC)",
    )


class LogResponseDTO(BaseModel):
    id: str
    source: str
    message: str
    level: LogLevel
    timestamp: datetime
    received_at: datetime
    host: Optional[str] = None
