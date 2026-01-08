from typing import List


class AnalysisResult:
    def __init__(
        self,
        summary: str,
        severity: str,
        confidence: float,
        suspected_causes: List[str],
        recommended_actions: List[str],
    ):
        self.summary = summary
        self.severity = severity
        self.confidence = confidence
        self.suspected_causes = suspected_causes
        self.recommended_actions = recommended_actions
