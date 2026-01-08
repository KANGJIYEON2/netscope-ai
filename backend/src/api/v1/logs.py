from fastapi import APIRouter

from schemas import LogCreateDTO, LogResponseDTO
from schemas.enums import LogLevel
from log.service import LogService
from infrastructure.storage import get_log_storage

router = APIRouter(prefix="/logs", tags=["logs"])

storage = get_log_storage()
service = LogService(storage)


@router.post("", response_model=LogResponseDTO)
def create_log(dto: LogCreateDTO):
    log_id, log = service.create(
        source=dto.source,
        message=dto.message,
        level=dto.level.value,   # Enum -> str
        timestamp=dto.timestamp,
    )

    return LogResponseDTO(
        id=log_id,
        source=log.source,
        message=log.message,
        level=LogLevel(log.level),  # str -> Enum
        timestamp=log.timestamp,
        received_at=log.received_at,
    )


@router.get("", response_model=list[LogResponseDTO])
def list_logs():
    items = service.list()
    return [
        LogResponseDTO(
            id=log_id,
            source=log.source,
            message=log.message,
            level=LogLevel(log.level),
            timestamp=log.timestamp,
            received_at=log.received_at,
        )
        for log_id, log in items
    ]
