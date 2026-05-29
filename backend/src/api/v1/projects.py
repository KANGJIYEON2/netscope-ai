from datetime import datetime, timedelta, UTC

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api.v1.dep import get_current_context
from src.db.session import get_db
from src.domain.project import ProjectDomainService
from src.model.log import Log
from src.model.analysis_result import AnalysisResult
from src.repositories.project_repository import ProjectRepository
from src.schemas.project import (
    ProjectCreateRequest,
    ProjectResponse,
)

router = APIRouter(prefix="/projects", tags=["projects"])


# ======================================================
# 1️⃣ 프로젝트 목록 조회
# ======================================================
@router.get("", response_model=list[ProjectResponse])
def list_projects(
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    repo = ProjectRepository(db)
    service = ProjectDomainService(repo)

    projects = service.list_projects(ctx["tenant_id"])

    return [
        {
            "id": p.id,
            "name": p.name,
            "created_at": p.created_at.isoformat(),
        }
        for p in projects
    ]


# ======================================================
# 2️⃣ 프로젝트 생성
# ======================================================
@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    req: ProjectCreateRequest,
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    repo = ProjectRepository(db)
    service = ProjectDomainService(repo)

    project = service.create_project(
        tenant_id=ctx["tenant_id"],
        name=req.name,
    )

    return {
        "id": project.id,
        "name": project.name,
        "created_at": project.created_at.isoformat(),
    }


# ======================================================
# 3️⃣ 프로젝트 개요 (대시보드)
# ======================================================
@router.get("/overview")
def project_overview(
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    """전체 프로젝트 대시보드: 24h 로그 수, 에러율, 최근 분석."""
    tenant_id = ctx["tenant_id"]
    since = datetime.now(UTC) - timedelta(hours=24)

    # 24h 로그 수
    log_count_24h = (
        db.query(func.count(Log.id))
        .filter(Log.tenant_id == tenant_id, Log.received_at >= since)
        .scalar()
    ) or 0

    # 24h 에러 수 → 에러율
    error_count = (
        db.query(func.count(Log.id))
        .filter(
            Log.tenant_id == tenant_id,
            Log.received_at >= since,
            Log.level == "ERROR",
        )
        .scalar()
    ) or 0

    error_rate = round(error_count / log_count_24h, 4) if log_count_24h else 0.0

    # 최근 분석 결과
    last = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.tenant_id == tenant_id)
        .order_by(AnalysisResult.received_at.desc())
        .first()
    )

    last_analysis = None
    if last:
        last_analysis = {
            "confidence": last.confidence,
            "severity": last.severity.value if last.severity else None,
            "created_at": last.received_at.isoformat(),
        }

    return {
        "log_count_24h": log_count_24h,
        "error_rate": error_rate,
        "last_analysis": last_analysis,
    }


# ======================================================
# 4️⃣ 프로젝트 삭제
# ======================================================
@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    repo = ProjectRepository(db)
    service = ProjectDomainService(repo)

    ok = service.delete_project(
        tenant_id=ctx["tenant_id"],
        project_id=project_id,
    )

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )