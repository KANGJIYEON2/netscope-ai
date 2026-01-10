from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, UTC

from src.db.base import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)

    tenant_id = Column(String, nullable=False, index=True)
    name = Column(String(100), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
