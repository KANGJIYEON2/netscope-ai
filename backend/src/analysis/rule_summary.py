from collections import Counter
from typing import List, Dict


def build_rule_summary(signals: List[Dict]) -> str:
    """
    DB에 저장된 rule signals 기반 요약
    - 추론 ❌
    - 관측 사실만 요약
    """

    if not signals:
        return "최근 7일간 유의미한 장애 신호는 감지되지 않았습니다."

    counter = Counter(s["rule_id"] for s in signals)

    parts = [
        f"{rule_id}({count}회)"
        for rule_id, count in counter.most_common()
    ]

    return (
        "최근 7일간 다음 장애 패턴이 반복 감지되었습니다: "
        + ", ".join(parts)
    )