from sqlalchemy import Column, String, DateTime
from datetime import datetime, UTC
from src.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)

    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)

    tenant_id = Column(String, nullable=False, index=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
