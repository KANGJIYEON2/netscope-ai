from dataclasses import dataclass


@dataclass(frozen=True)
class Signal:
    type: str
    rule_id: str
    score: float
    count: int