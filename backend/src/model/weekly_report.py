from sqlalchemy import Column, String, Date, DateTime, Integer, Text
from datetime import datetime, UTC

from src.db.base import Base


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id = Column(String, primary_key=True, index=True)

    tenant_id = Column(String, nullable=False, index=True)
    project_id = Column(String, nullable=False, index=True)

    # ===== 기간 =====
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # ===== 요약 =====
    report_count = Column(Integer, nullable=False)

    summary = Column(Text, nullable=False)

    # ===== 리스크 =====
    risk_level = Column(String, nullable=False)   # 낮음 / 보통 / 높음 / UNKNOWN
    risk_reason = Column(Text, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
