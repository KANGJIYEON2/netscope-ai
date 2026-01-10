from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.dep import get_current_context
from src.db.session import get_db
from src.domain.project import ProjectDomainService
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
# 3️⃣ 프로젝트 삭제
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