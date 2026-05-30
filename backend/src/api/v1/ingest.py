from fastapi import APIRouter, Header, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.schemas.ingest import IngestPayload
from src.ingest.service import ingest_logs
from src.db.session import get_db
from src.core.config import settings

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("")
def ingest(
    payload: IngestPayload,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_project_id: str = Header(..., alias="X-Project-ID"),
    x_agent_id: str | None = Header(default=None, alias="X-Agent-ID"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
):
    # Optional shared-secret auth for agents (enabled only when INGEST_API_KEY set).
    if settings.INGEST_API_KEY and x_api_key != settings.INGEST_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing X-API-Key",
        )

    ingest_logs(
        db=db,
        tenant_id=x_tenant_id,
        project_id=x_project_id,
        agent_id=x_agent_id,
        raw_logs=payload.logs,
    )
    return {"status": "ok"}
