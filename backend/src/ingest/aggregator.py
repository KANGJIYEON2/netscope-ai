from ingest.signals import extract_signals
from ingest.persist import persist_analysis


class SignalAggregator:
    def update(self, *, tenant_id: str, project_id: str, matches: list) -> None:
        signals = extract_signals(matches)

        confidence = min(
            sum(s["score"] * s["count"] for s in signals),
            1.0,
        )

        aggregated = {
            "confidence": confidence,
            "signals": signals,
        }

        persist_analysis(
            tenant_id=tenant_id,
            project_id=project_id,
            aggregated=aggregated,
        )
