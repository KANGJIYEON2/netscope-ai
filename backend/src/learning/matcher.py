"""
PatternMatcher — matches incoming logs against the pattern catalog.

Used during analysis to find known patterns and include their history
in the analysis result (L2).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.learning.masking import mask_variables
from src.learning.drain import DrainTree
from src.model.pattern import Pattern


def match_patterns(
    *,
    db: Session,
    tenant_id: str,
    messages: list[str],
) -> list[dict]:
    """
    Match raw log messages against the tenant's pattern catalog.

    Returns a list of matched patterns with their history:
    - labeled/promoted patterns contribute scores
    - candidate patterns are included as reference only (score=0)
    """
    # Build a temp Drain tree from messages to get cluster IDs
    tree = DrainTree(depth=4, sim_threshold=0.4)
    cluster_ids: set[str] = set()

    for msg in messages:
        masked = mask_variables(msg)
        cluster = tree.add(masked)
        cluster_ids.add(cluster.cluster_id)

    if not cluster_ids:
        return []

    # Lookup patterns in DB
    patterns = (
        db.query(Pattern)
        .filter(
            Pattern.tenant_id == tenant_id,
            Pattern.id.in_(cluster_ids),
            Pattern.status != "dismissed",
        )
        .all()
    )

    result = []
    for p in patterns:
        effective_score = 0.0
        if p.status in ("labeled", "promoted"):
            effective_score = p.score_seed + p.score_adjust

        # Compute average severity from level_dist
        avg_severity = _avg_severity(p.level_dist or {})

        result.append({
            "pattern_id": p.id,
            "label": p.label,
            "display_name": p.display_name,
            "template": p.template,
            "score": round(effective_score, 4),
            "status": p.status,
            "history": {
                "total_count": p.total_count,
                "last_seen": p.last_seen.isoformat() if p.last_seen else None,
                "avg_severity": avg_severity,
                "confirm_count": p.confirm_count,
                "dismiss_count": p.dismiss_count,
            },
        })

    return result


def _avg_severity(level_dist: dict) -> str:
    """Estimate average severity from level distribution."""
    weights = {"ERROR": 3, "FATAL": 3, "CRITICAL": 3, "WARN": 2, "WARNING": 2, "INFO": 1, "DEBUG": 0}
    total = 0
    weighted = 0
    for level, count in level_dist.items():
        w = weights.get(level.upper(), 1)
        weighted += w * count
        total += count
    if total == 0:
        return "LOW"
    avg = weighted / total
    if avg >= 2.5:
        return "HIGH"
    if avg >= 1.5:
        return "MEDIUM"
    return "LOW"
