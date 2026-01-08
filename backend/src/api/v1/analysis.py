from fastapi import APIRouter, HTTPException

from schemas import AnalysisRequestDTO, AnalysisResultDTO
from infrastructure.storage import get_log_storage
from analysis.engine import AnalysisEngine

router = APIRouter(prefix="/analysis", tags=["analysis"])

storage = get_log_storage()
engine = AnalysisEngine()


@router.post("", response_model=AnalysisResultDTO)
def analyze(dto: AnalysisRequestDTO):
    found, missing = storage.get_many(dto.log_ids)
    if missing:
        raise HTTPException(status_code=400, detail={"message": "log_id not found", "missing": missing})

    logs = [log for _, log in found]
    result = engine.analyze(logs, dto.strategy)

    return AnalysisResultDTO(**result)
