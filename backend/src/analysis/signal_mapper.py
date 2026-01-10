from collections import Counter
from src.analysis.rule_engine import RuleMatch
from src.analysis.signal import Signal


def extract_signals(matches: list[RuleMatch]) -> list[Signal]:
    counter = Counter(m.rule_id for m in matches)

    signals = []
    for m in matches:
        signals.append(
            Signal(
                type=m.rule_id.lower(),  # or 명시적 매핑
                rule_id=m.rule_id,
                score=m.score,
                count=counter[m.rule_id],
            )
        )

    # rule_id 중복 제거
    unique = {s.rule_id: s for s in signals}
    return list(unique.values())