from typing import List

from analysis.rule_engine import RuleEngine, default_rules, aggregate
from analysis.gpt_analyzer import GPTAnalyzer
from schemas.enums import SeverityLevel, AnalysisStrategy
from log.models import Log


class AnalysisEngine:
    def __init__(self):
        self.rule_engine = RuleEngine(default_rules())
        self.gpt = GPTAnalyzer()

    def analyze(self, logs: List[Log], strategy: AnalysisStrategy):
        # 1️⃣ Rule Engine (deterministic baseline)
        matches = self.rule_engine.run(logs)
        rule_result = aggregate(matches)

        # 기본은 rule 결과 그대로
        result = dict(rule_result)
        strategy_used = "rule"

        # 2️⃣ GPT 보강 (선택적 확장)
        if strategy == AnalysisStrategy.GPT and self.gpt.is_enabled():
            g = self.gpt.analyze(
                logs=logs,
                rule_summary=rule_result["summary"],
                rule_causes=rule_result["suspected_causes"],
                rule_actions=rule_result["recommended_actions"],
            )

            strategy_used = "gpt"

            # confidence는 "보너스" 개념으로만 증가
            bonus = float(g.get("confidence_bonus", 0.0))
            result["confidence"] = min(result["confidence"] + bonus, 1.0)

            # causes / actions 병합 (중복 제거)
            result["suspected_causes"] = (
                result["suspected_causes"]
                + [c for c in g.get("suspected_causes", []) if c not in result["suspected_causes"]]
            )

            result["recommended_actions"] = (
                result["recommended_actions"]
                + [a for a in g.get("recommended_actions", []) if a not in result["recommended_actions"]]
            )

            # summary는 GPT가 덮어쓸 수 있음
            result["summary"] = g.get("summary", result["summary"])

        # 3️⃣ Severity 계산 (confidence 기반)
        confidence = result["confidence"]

        if confidence >= 0.75:
            severity = SeverityLevel.HIGH
        elif confidence >= 0.45:
            severity = SeverityLevel.MEDIUM
        else:
            severity = SeverityLevel.LOW

        result["severity"] = severity
        result["strategy_used"] = strategy_used

        # 4️⃣ 응답 안정성 (빈 값 보호)
        if not result["suspected_causes"]:
            result["suspected_causes"] = ["명확한 패턴 미검출 (추가 로그 필요)"]

        if not result["recommended_actions"]:
            result["recommended_actions"] = ["추가 로그 수집 후 ERROR/timeout/5xx 패턴 재분석"]

        return result
