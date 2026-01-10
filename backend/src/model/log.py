from sqlalchemy import Column, String, DateTime, Enum as SAEnum
from datetime import datetime, UTC

from db.base import Base
from schemas.enums import LogLevel


class Log(Base):
    __tablename__ = "logs"

    id = Column(String, primary_key=True)

    # 🔥 멀티테넌시 / 프로젝트 단위
    tenant_id = Column(String(50), nullable=False, index=True)
    project_id = Column(String(100), nullable=False, index=True)

    # 🔥 로그 출처 (어디서 왔는지)
    source = Column(String(50), nullable=False)
    # ex) gateway, nginx, app, cron, shell

    # 🔥 로그 생성 방식
    source_type = Column(String(20), nullable=False)
    # agent | manual

    message = Column(String, nullable=False)

    level = Column(
        SAEnum(LogLevel, name="log_level"),
        nullable=False,
        default=LogLevel.INFO,
    )

    # 🔥 실제 로그 발생 시각
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # 🔥 우리 시스템이 받은 시각
    received_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # 선택 정보
    host = Column(String, nullable=True)
