from analysis.result import AnalysisResult
from analysis.rules import ConfidenceRules
from schemas.enums import SeverityLevel


class AnalysisEngine:
    def __init__(self):
        self.rules = ConfidenceRules()

    def analyze(self, logs):
        confidence = self.rules.calculate(logs)

        severity = (
            SeverityLevel.HIGH
            if confidence > 0.7
            else SeverityLevel.MEDIUM
        )

        return AnalysisResult(
            summary="로그 패턴 분석 결과",
            severity=severity,
            confidence=confidence,
            suspected_causes=["DB connection timeout"],
            recommended_actions=["DB connection pool 점검"],
        )
