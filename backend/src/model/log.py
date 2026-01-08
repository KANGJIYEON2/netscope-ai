from sqlalchemy import Column, String, DateTime, Enum as SAEnum
from datetime import datetime, UTC

from db.base import Base
from schemas.enums import LogLevel


class Log(Base):
    __tablename__ = "logs"

    id = Column(String, primary_key=True)
    source = Column(String(50), nullable=False)
    message = Column(String, nullable=False)

    level = Column(
        SAEnum(LogLevel, name="log_level"),
        nullable=False,
        default=LogLevel.INFO,
    )

    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    received_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    host = Column(String, nullable=True)