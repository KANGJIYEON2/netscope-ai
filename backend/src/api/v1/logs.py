from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.dep import get_current_context
from src.db.session import get_db
from src.domain.log import LogDomainService
from src.model.log import Log
from src.schemas.log import LogCreateDTO, LogResponseDTO

router = APIRouter(
    prefix="/projects/{project_id}/logs",
    tags=["logs"],
)

# ======================================================
# 1️⃣ 로그 생성 (manual)
# ======================================================
@router.post(
    "",
    response_model=LogResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
def create_log(
    project_id: str,
    dto: LogCreateDTO,
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    service = LogDomainService(db)

    log = service.create_log(
        tenant_id=ctx["tenant_id"],
        project_id=project_id,
        source=dto.source,
        message=dto.message,
        level=dto.level,
        source_type="manual",
        timestamp=dto.timestamp,
    )

    return LogResponseDTO(
        id=log.id,
        source=log.source,
        message=log.message,
        level=log.level,
        timestamp=log.timestamp,
        received_at=log.received_at,
        host=log.host,
    )


# ======================================================
# 2️⃣ 프로젝트 로그 목록 조회
# ======================================================
@router.get("", response_model=list[LogResponseDTO])
def list_logs(
    project_id: str,
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    logs = (
        db.query(Log)
        .filter(
            Log.tenant_id == ctx["tenant_id"],
            Log.project_id == project_id,
        )
        .order_by(Log.timestamp.desc())
        .limit(200)
        .all()
    )

    return [
        LogResponseDTO(
            id=l.id,
            source=l.source,
            message=l.message,
            level=l.level,
            timestamp=l.timestamp,
            received_at=l.received_at,
            host=l.host,
        )
        for l in logs
    ]


# ======================================================
# 3️⃣ 로그 삭제 (단건)
# ======================================================
@router.delete(
    "/{log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_log(
    project_id: str,
    log_id: str,
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    log = (
        db.query(Log)
        .filter(
            Log.id == log_id,
            Log.tenant_id == ctx["tenant_id"],
            Log.project_id == project_id,
        )
        .first()
    )

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found",
        )

    db.delete(log)
    db.commit()
