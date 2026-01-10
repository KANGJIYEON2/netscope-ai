from src.analysis.rule_engine import RuleEngine, default_rules
from src.ingest.aggregator import SignalAggregator

# 싱글톤 구성 (hot path)
rule_engine = RuleEngine(default_rules())
aggregator = SignalAggregator()


def ingest_logs(*, tenant_id: str, project_id: str, agent_id: str | None, raw_logs: list[str]):
    """
    Ingestion hot path:
    - No DB writes
    - No raw log persistence
    """
    matches = rule_engine.run_raw(raw_logs)

    aggregator.update(
        tenant_id=tenant_id,
        project_id=project_id,
        matches=matches,
    )