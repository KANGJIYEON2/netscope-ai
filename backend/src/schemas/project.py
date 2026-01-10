from pydantic import BaseModel, Field
from datetime import datetime


class ProjectCreateRequest(BaseModel):
    """
    프로젝트 생성 요청
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Project name",
    )


class ProjectResponse(BaseModel):
    """
    프로젝트 응답 DTO
    """
    id: str
    name: str
    created_at: datetime
