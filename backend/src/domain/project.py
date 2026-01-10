import uuid
from src.repositories.project_repository import ProjectRepository
from src.model.Project import Project


class ProjectDomainService:
    def __init__(self, repo: ProjectRepository):
        self.repo = repo

    def list_projects(self, tenant_id: str):
        return self.repo.list_by_tenant(tenant_id)

    def create_project(self, tenant_id: str, name: str):
        project = Project(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
        )
        return self.repo.create(project)

    def delete_project(self, tenant_id: str, project_id: str):
        project = self.repo.get(tenant_id, project_id)
        if not project:
            return False

        self.repo.delete(project)
        return True
