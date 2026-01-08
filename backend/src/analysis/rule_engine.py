from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Callable, List, Set, Tuple, Dict

from schemas.enums import LogLevel


# ======================================================
# Ephemeral Log (Rule-only, NOT ORM)
# ======================================================

@dataclass(frozen=True)
class RuleLog:
    """
    In-memory log representation for rule evaluation.
    - NOT persisted
    - NOT SQLAlchemy
    """
    source: str
    message: str
    level: LogLevel
    timestamp: datetime


# ======================================================
# Rule Match Result
# ======================================================

@dataclass(frozen=True)
class RuleMatch:
    rule_id: str
    title: str
    score: float
    evidence: str
    causes: Tuple[str, ...]
    actions: Tuple[str, ...]


# ======================================================
# Rule Definition
# ======================================================

class Rule:
    """
    Rule-based Expert System Component

    - Deterministic
    - Explainable
    - Baseline reasoning (no probabilistic guess)
    """

    def __init__(
        self,
        rule_id: str,
        title: str,
        score: float,
        predicate: Callable[[List[RuleLog]], bool],
        evidence_builder: Callable[[List[RuleLog]], str],
        causes: List[str],
        actions: List[str],
    ):
        self.rule_id = rule_id
        self.title = title
        self.score = score
        self.predicate = predicate
        self.evidence_builder = evidence_builder
        self.causes = tuple(causes)
        self.actions = tuple(actions)

    def evaluate(self, logs: List[RuleLog]) -> RuleMatch | None:
        if not self.predicate(logs):
            return None

        return RuleMatch(
            rule_id=self.rule_id,
            title=self.title,
            score=self.score,
            evidence=self.evidence_builder(logs),
            causes=self.causes,
            actions=self.actions,
        )


# ======================================================
# Rule Engine
# ======================================================

class RuleEngine:
    def __init__(self, rules: List[Rule]):
        self.rules = rules

    def run(self, logs: List[RuleLog]) -> List[RuleMatch]:
        matches: List[RuleMatch] = []
        for rule in self.rules:
            result = rule.evaluate(logs)
            if result:
                matches.append(result)
        return matches

    # --------------------------------------------------
    # Ingestion Adapter (raw → RuleLog)
    # --------------------------------------------------
    def run_raw(self, raw_logs: List[str]) -> List[RuleMatch]:
        """
        Adapter for ingestion pipeline.
        - Converts raw log lines into RuleLog
        - No DB persistence
        """
        now = datetime.now(UTC)

        logs = [
            RuleLog(
                source="ingest",
                message=line,
                level=self._infer_level(line),
                timestamp=now,
            )
            for line in raw_logs
        ]

        return self.run(logs)

    def _infer_level(self, line: str) -> LogLevel:
        upper = line.upper()
        if "ERROR" in upper:
            return LogLevel.ERROR
        if "WARN" in upper:
            return LogLevel.WARN
        if "DEBUG" in upper:
            return LogLevel.DEBUG
        return LogLevel.INFO


# ======================================================
# Regex Patterns (Signal Extractors)
# ======================================================

_TIMEOUT_RE = re.compile(r"\b(timeout|timed out|ETIMEDOUT)\b", re.IGNORECASE)
_CONN_RE = re.compile(r"\b(connection refused|ECONNREFUSED|reset by peer)\b", re.IGNORECASE)
_DNS_RE = re.compile(r"\b(ENOTFOUND|DNS|name resolution|NXDOMAIN)\b", re.IGNORECASE)
_5XX_RE = re.compile(r"\b(5\d\d|502|503|504)\b", re.IGNORECASE)


# ======================================================
# Helper Functions
# ======================================================

def _any_level(level: LogLevel, logs: List[RuleLog]) -> bool:
    return any(log.level == level for log in logs)


def _any_message_regex(regex: re.Pattern, logs: List[RuleLog]) -> bool:
    return any(regex.search(log.message or "") for log in logs)


def _count_by_source(logs: List[RuleLog]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for log in logs:
        counts[log.source] = counts.get(log.source, 0) + 1
    return counts


# ======================================================
# Default Rule Set (v1.0)
# ======================================================

def default_rules() -> List[Rule]:
    return [
        Rule(
            rule_id="R001",
            title="Timeout 발생",
            score=0.35,
            predicate=lambda logs: _any_message_regex(_TIMEOUT_RE, logs),
            evidence_builder=lambda logs: (
                "로그 메시지에 timeout / timed out / ETIMEDOUT 키워드가 포함됨"
            ),
            causes=[
                "Upstream(서버/DB/API) 응답 지연",
                "네트워크 지연 또는 패킷 손실",
                "과부하로 인한 요청 처리 지연",
            ],
            actions=[
                "클라이언트 및 게이트웨이 타임아웃 설정값 확인",
                "Upstream 서비스 상태 및 부하 점검",
                "네트워크 경로(라우팅/방화벽/NAT) 확인",
            ],
        ),

        Rule(
            rule_id="R002",
            title="Connection 실패",
            score=0.35,
            predicate=lambda logs: _any_message_regex(_CONN_RE, logs),
            evidence_builder=lambda logs: (
                "connection refused 또는 reset by peer 관련 키워드가 로그에 포함됨"
            ),
            causes=[
                "대상 포트에서 서비스가 리스닝되지 않음",
                "방화벽 또는 보안그룹에 의해 연결 차단",
                "상대 서비스 비정상 종료",
            ],
            actions=[
                "대상 서버에서 포트 리스닝 여부 확인",
                "방화벽/보안그룹 규칙 확인",
                "상대 서비스 헬스체크 수행",
            ],
        ),

        Rule(
            rule_id="R003",
            title="DNS / Name Resolution 문제",
            score=0.25,
            predicate=lambda logs: _any_message_regex(_DNS_RE, logs),
            evidence_builder=lambda logs: (
                "DNS / name resolution 관련 에러 키워드가 로그에 포함됨"
            ),
            causes=[
                "DNS 레코드 미등록 또는 오타",
                "DNS 리졸버 또는 네임서버 장애",
                "컨테이너/VPC DNS 설정 오류",
            ],
            actions=[
                "A/AAAA 레코드 존재 여부 확인",
                "nslookup / dig 결과 확인",
                "배포 환경 DNS 설정 점검",
            ],
        ),

        Rule(
            rule_id="R004",
            title="5xx 응답 감지",
            score=0.25,
            predicate=lambda logs: _any_message_regex(_5XX_RE, logs),
            evidence_builder=lambda logs: (
                "로그 메시지에 5xx(502/503/504) 상태 코드 패턴이 포함됨"
            ),
            causes=[
                "Upstream 애플리케이션 내부 오류",
                "프록시 또는 게이트웨이 오류",
                "트래픽 급증으로 인한 과부하",
            ],
            actions=[
                "Upstream 애플리케이션 로그 확인",
                "프록시/게이트웨이 에러 로그 확인",
                "리소스 사용량 및 오토스케일 설정 점검",
            ],
        ),

        Rule(
            rule_id="R005",
            title="ERROR 레벨 로그 존재",
            score=0.20,
            predicate=lambda logs: _any_level(LogLevel.ERROR, logs),
            evidence_builder=lambda logs: (
                "level=ERROR 로 기록된 로그가 하나 이상 존재함"
            ),
            causes=[
                "애플리케이션 또는 시스템 오류 발생",
            ],
            actions=[
                "ERROR 로그 타임라인 기반 상관관계 분석",
                "최근 배포/설정 변경 이력 확인",
            ],
        ),

        Rule(
            rule_id="R006",
            title="특정 source 로그 급증",
            score=0.20,
            predicate=lambda logs: any(v >= 5 for v in _count_by_source(logs).values()),
            evidence_builder=lambda logs: (
                "동일 source에서 로그가 5회 이상 반복 발생함"
            ),
            causes=[
                "특정 컴포넌트 반복 오류",
                "재시도 로직 또는 무한 루프 가능성",
            ],
            actions=[
                "해당 컴포넌트 상세 로그 및 메트릭 확인",
                "재시도 정책 및 서킷 브레이커 설정 점검",
            ],
        ),
    ]


# ======================================================
# Explainable Aggregation Logic
# ======================================================

def build_rule_summary(matches: List[RuleMatch]) -> str:
    if not matches:
        return "룰 기반 분석 결과, 특이 장애 징후는 감지되지 않았습니다."

    titles = ", ".join(m.title for m in matches)
    return f"룰 기반 분석 결과, 다음과 같은 이상 징후가 감지되었습니다: {titles}."


def evidence_count_bonus(matches: List[RuleMatch]) -> float:
    count = len(matches)
    if count >= 4:
        return 0.15
    if count == 3:
        return 0.10
    if count == 2:
        return 0.05
    return 0.0


def interaction_bonus(matches: List[RuleMatch]) -> float:
    rule_ids = {m.rule_id for m in matches}
    bonus = 0.0

    if {"R001", "R004"} <= rule_ids:
        bonus += 0.15
    if {"R001", "R005"} <= rule_ids:
        bonus += 0.10
    if {"R002", "R003"} <= rule_ids:
        bonus += 0.10

    return bonus


def confidence_level(score: float) -> str:
    if score >= 0.75:
        return "HIGH"
    if score >= 0.45:
        return "MEDIUM"
    return "LOW"


def aggregate(matches: List[RuleMatch]) -> Dict:
    base_score = sum(m.score for m in matches)
    bonus = evidence_count_bonus(matches) + interaction_bonus(matches)
    confidence = min(base_score + bonus, 1.0)

    causes: List[str] = []
    actions: List[str] = []
    seen_c: Set[str] = set()
    seen_a: Set[str] = set()
    matched_rules: List[str] = []

    for m in matches:
        matched_rules.append(
            f"{m.rule_id} {m.title} (+{m.score:.2f}) - {m.evidence}"
        )

        for c in m.causes:
            if c not in seen_c:
                seen_c.add(c)
                causes.append(c)

        for a in m.actions:
            if a not in seen_a:
                seen_a.add(a)
                actions.append(a)

    return {
        "strategy": "rule",
        "ruleset_version": "v1.0",
        "confidence": round(confidence, 2),
        "confidence_level": confidence_level(confidence),
        "summary": build_rule_summary(matches),
        "suspected_causes": causes,
        "recommended_actions": actions,
        "matched_rules": matched_rules,
    }
