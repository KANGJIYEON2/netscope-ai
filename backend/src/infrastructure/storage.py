import uuid
from typing import Dict, List, Optional, Tuple

from src.log.models import Log


class InMemoryLogStorage:
    def __init__(self):
        self._logs: Dict[str, Log] = {}

    def save(self, log: Log) -> str:
        log_id = str(uuid.uuid4())
        self._logs[log_id] = log
        return log_id

    def get(self, log_id: str) -> Optional[Log]:
        return self._logs.get(log_id)

    def get_many(self, log_ids: List[str]) -> Tuple[List[Tuple[str, Log]], List[str]]:
        found: List[Tuple[str, Log]] = []
        missing: List[str] = []
        for lid in log_ids:
            log = self._logs.get(lid)
            if log is None:
                missing.append(lid)
            else:
                found.append((lid, log))
        return found, missing

    def list(self) -> List[Tuple[str, Log]]:
        return list(self._logs.items())


# ✅ 싱글톤(전역 1개)로 공유
_storage_singleton = InMemoryLogStorage()


def get_log_storage() -> InMemoryLogStorage:
    return _storage_singleton
