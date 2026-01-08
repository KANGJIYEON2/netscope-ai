from collections import defaultdict
from datetime import datetime, timedelta


class SignalAggregator:
    """
    In-memory signal aggregation (7-day window)
    Raw logs are NEVER persisted.
    """

    def __init__(self):
        # key = (tenant_id, project_id)
        self.buffer = defaultdict(list)

    def update(self, *, tenant_id: str, project_id: str, matches: list[dict]):
        key = (tenant_id, project_id)
        now = datetime.utcnow()

        self.buffer[key].append((now, matches))
        self._prune_old(key)

    def _prune_old(self, key):
        cutoff = datetime.utcnow() - timedelta(days=7)
        self.buffer[key] = [
            (ts, matches)
            for ts, matches in self.buffer[key]
            if ts >= cutoff
        ]

    def get_window(self, tenant_id: str, project_id: str):
        return self.buffer.get((tenant_id, project_id), [])