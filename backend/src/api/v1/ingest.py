from fastapi import APIRouter, Header, Depends
from sqlalchemy.orm import Session

from src.schemas.ingest import IngestPayload
from src.ingest.service import ingest_logs
from src.db.session import get_db

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("")
def ingest(
    payload: IngestPayload,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_project_id: str = Header(..., alias="X-Project-ID"),
    x_agent_id: str | None = Header(default=None, alias="X-Agent-ID"),
    db: Session = Depends(get_db),
):
    ingest_logs(
        db=db,
        tenant_id=x_tenant_id,
        project_id=x_project_id,
        agent_id=x_agent_id,
        raw_logs=payload.logs,
    )
    return {"status": "ok"}
