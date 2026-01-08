from collections import Counter
from typing import List
from analysis.rule_engine import RuleMatch


def extract_signals(matches: List[RuleMatch]) -> list[dict]:
    counter = Counter(m.rule_id for m in matches)

    signals = []
    for m in matches:
        if any(s["rule_id"] == m.rule_id for s in signals):
            continue

        signals.append({
            "rule_id": m.rule_id,
            "score": m.score,
            "count": counter[m.rule_id],
        })

    return signals