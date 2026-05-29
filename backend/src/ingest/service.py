import logging

from sqlalchemy.orm import Session

from src.analysis.rule_engine import RuleEngine, default_rules
from src.ingest.aggregator import SignalAggregator
from src.ingest.parser import parse_log_lines

logger = logging.getLogger(__name__)

# 싱글톤 구성 (hot path)
rule_engine = RuleEngine(default_rules())
aggregator = SignalAggregator()


def ingest_logs(*, db: Session, tenant_id: str, project_id: str, agent_id: str | None, raw_logs: list[str]):
    """
    Ingestion hot path:
    - Rule engine evaluation
    - Pattern mining (L0 — background collection)
    - No raw log persistence
    """
    matches = rule_engine.run_raw(raw_logs)

    aggregator.update(
        tenant_id=tenant_id,
        project_id=project_id,
        matches=matches,
    )

    # L0: Background pattern mining
    try:
        from src.learning.catalog import mine_and_upsert

        parsed = parse_log_lines(raw_logs)
        mine_and_upsert(
            db=db,
            tenant_id=tenant_id,
            messages=raw_logs,
            sources=[p.source for p in parsed],
            levels=[p.level for p in parsed],
        )
    except Exception as e:
        # Pattern mining failure must not break ingest
        logger.warning(f"Pattern mining failed (non-fatal): {e}")