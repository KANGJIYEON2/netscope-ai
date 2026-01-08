from datetime import datetime, UTC
from typing import Optional

from .models import Log
from infrastructure.storage import InMemoryLogStorage


class LogService:
    def __init__(self, storage: InMemoryLogStorage):
        self.storage = storage

    def create(
        self,
        *,
        source: str,
        message: str,
        level: str,
        timestamp: Optional[datetime],
    ):
        log = Log(
            source=source,
            message=message,
            level=level,
            timestamp=timestamp or datetime.now(UTC),
            received_at=datetime.now(UTC),
        )

        log_id = self.storage.save(log)
        return log_id, log

    def list(self):
        return self.storage.list()
