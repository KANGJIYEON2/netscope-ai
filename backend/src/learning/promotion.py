"""
Pattern auto-promotion logic (L3).

Checks if a labeled pattern should be promoted to full rule status
based on confirm/dismiss feedback ratios.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.model.pattern import Pattern


# Promotion thresholds
MIN_CONFIRMS = 5
MAX_DISMISS_RATIO = 0.20  # dismiss / (confirm + dismiss) < 20%


def check_and_promote(db: Session, pattern: Pattern) -> bool:
    """
    Check if a labeled pattern should be auto-promoted.
    Returns True if promotion occurred.
    """
    if pattern.status != "labeled":
        return False

    if pattern.confirm_count < MIN_CONFIRMS:
        return False

    total_feedback = pattern.confirm_count + pattern.dismiss_count
    if total_feedback == 0:
        return False

    dismiss_ratio = pattern.dismiss_count / total_feedback
    if dismiss_ratio >= MAX_DISMISS_RATIO:
        return False

    pattern.status = "promoted"
    db.commit()
    return True


def check_demotion(db: Session, pattern: Pattern) -> bool:
    """
    Check if a promoted pattern should be demoted back to labeled
    due to excessive dismissals.
    """
    if pattern.status != "promoted":
        return False

    total_feedback = pattern.confirm_count + pattern.dismiss_count
    if total_feedback < MIN_CONFIRMS:
        return False

    dismiss_ratio = pattern.dismiss_count / total_feedback
    if dismiss_ratio >= MAX_DISMISS_RATIO:
        pattern.status = "labeled"
        db.commit()
        return True

    return False
