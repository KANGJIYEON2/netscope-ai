import os
from typing import List

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from log.models import Log


class GPTAnalyzer:
    """
    GPT 기반 분석 보조 엔진
    - RuleEngine 결과를 기준선(baseline)으로 사용
    - Raw logs + Rule 결과를 함께 전달하여 보강 분석
    """

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None

    def is_enabled(self) -> bool:
        return self.client is not None

    def analyze(
        self,
        *,
        logs: List[Log],
        rule_summary: str,
        rule_causes: List[str],
        rule_actions: List[str],
    ) -> dict:
        # GPT 비활성 → rule 결과 그대로 반환
        if not self.is_enabled():
            return {
                "summary": rule_summary,
                "suspected_causes": rule_causes,
                "recommended_actions": rule_actions,
                "confidence_bonus": 0.0,
            }

        # --- Raw Logs 텍스트 ---
        log_block = "\n".join(
            f"[{log.level}] {log.source}: {log.message}"
            for log in logs
        )

        # --- GPT Messages (타입 안전) ---
        messages: list[
            ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
        ] = [
            {
                "role": "system",
                "content": (
                    "You are a Site Reliability Engineer (SRE).\n"
                    "The rule-engine analysis is the baseline.\n"
                    "Do NOT contradict rules without clear justification.\n"
                    "Add deeper insight only if it strengthens the analysis."
                ),
            },
            {
                "role": "user",
                "content": f"""
[Rule Engine Summary]
{rule_summary}

[Rule Engine Suspected Causes]
- {"; ".join(rule_causes)}

[Rule Engine Recommended Actions]
- {"; ".join(rule_actions)}

[Raw Logs]
{log_block}
""".strip(),
            },
        ]

        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0.2,
        )

        gpt_text = response.choices[0].message.content.strip()

        return {
            "summary": gpt_text,
            "suspected_causes": rule_causes + ["LLM 기반 추가 추론"],
            "recommended_actions": rule_actions + ["GPT 제안 사항 검토"],
            "confidence_bonus": 0.2,
        }
