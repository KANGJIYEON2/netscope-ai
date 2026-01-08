from pydantic import BaseModel, Field
from datetime import datetime, UTC
from typing import Optional
from .enums import LogLevel


class LogCreateDTO(BaseModel):
    source: str = Field(
        ...,
        min_length=2,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        description="로그 발생 소스 (영문/숫자/_, - 만 허용)",
    )

    message: str = Field(
        ...,
        min_length=1,
        description="로그 메시지 (빈 문자열 불가)",
    )

    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="로그 레벨",
    )

    timestamp: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(UTC),
        description="로그 발생 시간 (UTC, 없으면 서버 기준)",
    )


class LogResponseDTO(BaseModel):
    id: Optional[str] = Field(None, description="로그 ID (DB 연동 시 채워짐)")
    source: str
    message: str
    level: LogLevel
    timestamp: datetime
    host: str | None = None
    received_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="서버 수신 시각 (UTC)",
    )
