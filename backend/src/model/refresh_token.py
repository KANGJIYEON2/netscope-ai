from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Index
from datetime import datetime, UTC
from src.db.base import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True)  # uuid 문자열로 넣어도 되고 (아래에서 jti 사용 추천)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    tenant_id = Column(String, nullable=False, index=True)

    # refresh JWT 전체를 해시해서 저장
    token_hash = Column(String, nullable=False)

    # refresh JWT 내부 jti 저장 (회전/폐기/재사용탐지에 좋음)
    jti = Column(String, nullable=False, unique=True, index=True)

    expires_at = Column(DateTime(timezone=True), nullable=False)

    revoked = Column(Boolean, nullable=False, default=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

Index("ix_refresh_tokens_user_tenant", RefreshToken.user_id, RefreshToken.tenant_id)