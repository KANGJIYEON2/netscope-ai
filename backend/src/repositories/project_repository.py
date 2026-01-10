from sqlalchemy.orm import Session
from src.model.Project import Project


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_tenant(self, tenant_id: str) -> list[Project]:
        return (
            self.db.query(Project)
            .filter(Project.tenant_id == tenant_id)
            .order_by(Project.created_at.desc())
            .all()
        )

    def get(self, tenant_id: str, project_id: str) -> Project | None:
        return (
            self.db.query(Project)
            .filter(
                Project.id == project_id,
                Project.tenant_id == tenant_id,
            )
            .first()
        )

    def create(self, project: Project) -> Project:
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project: Project):
        self.db.delete(project)
        self.db.commit()
