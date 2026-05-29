from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime, UTC

from src.db.base import Base


class Pattern(Base):
    __tablename__ = "patterns"

    id = Column(String, primary_key=True)  # sha1 prefix (12 chars)
    tenant_id = Column(String, nullable=False, index=True)

    # Template & sample
    template = Column(Text, nullable=False)
    sample = Column(Text, nullable=False)

    # Statistics
    total_count = Column(Integer, nullable=False, default=0)
    first_seen = Column(DateTime(timezone=True), nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=False)
    sources = Column(JSONB, nullable=False, default=dict)       # {source: count}
    level_dist = Column(JSONB, nullable=False, default=dict)    # {ERROR: 40, WARN: 7}
    hourly_dist = Column(ARRAY(Integer), nullable=False, default=[0] * 24)

    # Status & labeling
    status = Column(String, nullable=False, default="candidate")  # candidate|labeled|promoted|dismissed
    label = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    causes = Column(ARRAY(Text), nullable=False, default=[])
    actions = Column(ARRAY(Text), nullable=False, default=[])

    # Scoring
    score_seed = Column(Float, nullable=False, default=0.20)
    score_adjust = Column(Float, nullable=False, default=0.00)

    # Feedback counters
    confirm_count = Column(Integer, nullable=False, default=0)
    dismiss_count = Column(Integer, nullable=False, default=0)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class PatternFeedback(Base):
    __tablename__ = "pattern_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    pattern_id = Column(String, nullable=False, index=True)
    analysis_id = Column(String, nullable=True)
    action = Column(String, nullable=False)  # confirm | dismiss | wrong
    user_id = Column(String, nullable=True)
    severity_shown = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
