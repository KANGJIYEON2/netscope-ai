"""
Pattern Catalog — persists Drain clusters to the patterns table.

Called from the ingest pipeline to silently accumulate patterns
(L0 — background collection, no user-facing alerts yet).
"""
from __future__ import annotations

from datetime import datetime, UTC

from sqlalchemy.orm import Session

from src.learning.drain import DrainTree, LogCluster
from src.learning.masking import mask_variables
from src.model.pattern import Pattern


# Module-level singleton (shared across ingest calls within the process).
_drain_trees: dict[str, DrainTree] = {}

MAX_PATTERNS_PER_TENANT = 10_000


def _get_tree(tenant_id: str) -> DrainTree:
    if tenant_id not in _drain_trees:
        _drain_trees[tenant_id] = DrainTree()
    return _drain_trees[tenant_id]


def mine_and_upsert(
    *,
    db: Session,
    tenant_id: str,
    messages: list[str],
    sources: list[str] | None = None,
    levels: list[str] | None = None,
) -> list[LogCluster]:
    """
    Process raw log messages through Drain and upsert results into DB.

    Returns the list of LogClusters that the messages were assigned to.
    """
    tree = _get_tree(tenant_id)
    now = datetime.now(UTC)
    hour = now.hour

    clusters_seen: dict[str, LogCluster] = {}

    for i, msg in enumerate(messages):
        masked = mask_variables(msg)
        cluster = tree.add(masked)
        cid = cluster.cluster_id
        clusters_seen[cid] = cluster

        # Upsert pattern row
        pattern = (
            db.query(Pattern)
            .filter(Pattern.id == cid, Pattern.tenant_id == tenant_id)
            .first()
        )

        source = sources[i] if sources and i < len(sources) else "unknown"
        level = levels[i] if levels and i < len(levels) else "INFO"

        if pattern is None:
            # Check tenant limit
            count = (
                db.query(Pattern)
                .filter(Pattern.tenant_id == tenant_id)
                .count()
            )
            if count >= MAX_PATTERNS_PER_TENANT:
                # GC: remove oldest low-frequency candidate
                oldest = (
                    db.query(Pattern)
                    .filter(
                        Pattern.tenant_id == tenant_id,
                        Pattern.status == "candidate",
                    )
                    .order_by(Pattern.total_count.asc(), Pattern.last_seen.asc())
                    .first()
                )
                if oldest:
                    db.delete(oldest)

            pattern = Pattern(
                id=cid,
                tenant_id=tenant_id,
                template=cluster.template,
                sample=msg[:500],
                total_count=1,
                first_seen=now,
                last_seen=now,
                sources={source: 1},
                level_dist={level: 1},
                hourly_dist=_inc_hour([0] * 24, hour),
                status="candidate",
            )
            db.add(pattern)
        else:
            pattern.template = cluster.template
            pattern.total_count += 1
            pattern.last_seen = now
            pattern.updated_at = now

            # Merge source counts
            src_dict = dict(pattern.sources or {})
            src_dict[source] = src_dict.get(source, 0) + 1
            pattern.sources = src_dict

            # Merge level distribution
            lvl_dict = dict(pattern.level_dist or {})
            lvl_dict[level] = lvl_dict.get(level, 0) + 1
            pattern.level_dist = lvl_dict

            # Merge hourly distribution
            hdist = list(pattern.hourly_dist or [0] * 24)
            pattern.hourly_dist = _inc_hour(hdist, hour)

    db.commit()
    return list(clusters_seen.values())


def _inc_hour(dist: list[int], hour: int) -> list[int]:
    while len(dist) < 24:
        dist.append(0)
    dist[hour] += 1
    return dist
