from pydantic import BaseModel, Field
from typing import List


class IngestPayload(BaseModel):
    logs: List[str] = Field(
        ...,
        min_items=1,
        description="Raw log lines (stdout/stderr/system)",
    )