import uuid
from sqlalchemy.orm import Session
from datetime import datetime, UTC

from src.model.log import Log
from src.schemas.enums import LogLevel


class LogDomainService:
    def __init__(self, db: Session):
        self.db = db

    def create_log(
        self,
        *,
        tenant_id: str,
        project_id: str,
        source: str,
        message: str,
        level: LogLevel,
        source_type: str,  # manual | agent
        timestamp: datetime | None = None,
        host: str | None = None,
    ) -> Log:
        log = Log(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            project_id=project_id,
            source=source,
            source_type=source_type,
            message=message,
            level=level,
            timestamp=timestamp or datetime.now(UTC),
            received_at=datetime.now(UTC),
            host=host,
        )

        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        return log
