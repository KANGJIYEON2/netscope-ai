from fastapi import APIRouter

from schemas.analysis_test import TestAnalysisRequestDTO
from schemas.analysis import AnalysisResultDTO
from analysis.engine import AnalysisEngine

router = APIRouter(prefix="/analysis", tags=["analysis"])

engine = AnalysisEngine()


@router.post(
    "/test",
    response_model=AnalysisResultDTO,
)
def analyze_test(dto: TestAnalysisRequestDTO):
    result = engine.analyze_test(
        messages=dto.messages,
        strategy=dto.strategy,
    )

    return AnalysisResultDTO(**result)
