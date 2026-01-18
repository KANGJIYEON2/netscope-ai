from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Callable, List, Set, Tuple, Dict

from src.schemas.enums import LogLevel


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
_4XX_RE = re.compile(r"\b(4\d\d|401|403|404|429)\b", re.IGNORECASE)
_OOM_RE = re.compile(r"\b(out of memory|OOM|OutOfMemoryError|MemoryError)\b", re.IGNORECASE)
_DB_RE = re.compile(r"\b(database|DB|SQL|query|connection pool|deadlock)\b", re.IGNORECASE)
_DISK_RE = re.compile(r"\b(disk full|no space left|ENOSPC|storage)\b", re.IGNORECASE)
_CPU_RE = re.compile(r"\b(CPU|high load|overload|throttl)\b", re.IGNORECASE)
_AUTH_RE = re.compile(r"\b(authentication|authorization|unauthorized|forbidden|token|credential)\b", re.IGNORECASE)
_RATE_LIMIT_RE = re.compile(r"\b(rate limit|too many requests|throttle|quota)\b", re.IGNORECASE)
_CRASH_RE = re.compile(r"\b(crash|panic|segfault|core dump|fatal)\b", re.IGNORECASE)
_RESTART_RE = re.compile(r"\b(restart|reboot|killed|terminated)\b", re.IGNORECASE)
_SSL_RE = re.compile(r"\b(SSL|TLS|certificate|handshake)\b", re.IGNORECASE)
_PERMISSION_RE = re.compile(r"\b(permission denied|EACCES|access denied)\b", re.IGNORECASE)


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


def _count_matching_logs(regex: re.Pattern, logs: List[RuleLog]) -> int:
    return sum(1 for log in logs if regex.search(log.message or ""))


def _has_warn_level(logs: List[RuleLog]) -> bool:
    return any(log.level == LogLevel.WARN for log in logs)


# ======================================================
# Default Rule Set (v2.0)
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

        Rule(
            rule_id="R007",
            title="Out of Memory 감지",
            score=0.40,
            predicate=lambda logs: _any_message_regex(_OOM_RE, logs),
            evidence_builder=lambda logs: (
                "로그에 OOM / OutOfMemoryError / MemoryError 키워드가 포함됨"
            ),
            causes=[
                "메모리 누수(Memory Leak)",
                "할당된 메모리 부족",
                "대용량 데이터 처리 중 메모리 초과",
            ],
            actions=[
                "힙 덤프 분석 및 메모리 프로파일링",
                "컨테이너/인스턴스 메모리 할당량 증가",
                "메모리 사용량이 높은 코드 최적화",
            ],
        ),

        Rule(
            rule_id="R008",
            title="데이터베이스 관련 오류",
            score=0.30,
            predicate=lambda logs: (
                    _any_message_regex(_DB_RE, logs) and
                    (_any_level(LogLevel.ERROR, logs) or _has_warn_level(logs))
            ),
            evidence_builder=lambda logs: (
                "로그에 데이터베이스/SQL/쿼리 관련 키워드와 에러가 함께 포함됨"
            ),
            causes=[
                "DB 커넥션 풀 고갈",
                "느린 쿼리로 인한 타임아웃",
                "데드락 또는 락 경합",
                "DB 서버 과부하",
            ],
            actions=[
                "DB 커넥션 풀 설정 및 사용률 확인",
                "슬로우 쿼리 로그 분석",
                "DB 서버 리소스 및 락 상태 점검",
                "인덱스 및 쿼리 최적화",
            ],
        ),

        Rule(
            rule_id="R009",
            title="디스크 용량 부족",
            score=0.35,
            predicate=lambda logs: _any_message_regex(_DISK_RE, logs),
            evidence_builder=lambda logs: (
                "로그에 disk full / no space left / ENOSPC 키워드가 포함됨"
            ),
            causes=[
                "로그 파일 과다 적재",
                "임시 파일 정리 미흡",
                "디스크 할당량 초과",
            ],
            actions=[
                "디스크 사용량 확인 (df -h)",
                "대용량 파일 및 로그 정리",
                "볼륨 확장 또는 로그 로테이션 설정",
            ],
        ),

        Rule(
            rule_id="R010",
            title="CPU 과부하",
            score=0.25,
            predicate=lambda logs: _any_message_regex(_CPU_RE, logs),
            evidence_builder=lambda logs: (
                "로그에 CPU / high load / throttle 관련 키워드가 포함됨"
            ),
            causes=[
                "트래픽 급증",
                "비효율적인 알고리즘 또는 무한 루프",
                "컨테이너 CPU 제한 초과",
            ],
            actions=[
                "CPU 사용률 및 프로세스별 부하 확인",
                "부하 테스트 및 프로파일링",
                "오토스케일링 설정 및 리소스 할당 증가",
            ],
        ),

        Rule(
            rule_id="R011",
            title="인증/인가 실패",
            score=0.25,
            predicate=lambda logs: _any_message_regex(_AUTH_RE, logs) and _any_message_regex(_4XX_RE, logs),
            evidence_builder=lambda logs: (
                "로그에 인증/인가 관련 키워드와 4xx 에러가 함께 포함됨"
            ),
            causes=[
                "만료된 토큰 또는 자격증명",
                "권한 설정 오류",
                "인증 서비스 장애",
            ],
            actions=[
                "토큰 및 자격증명 유효성 확인",
                "IAM 정책 및 권한 설정 검토",
                "인증 서비스 로그 및 상태 점검",
            ],
        ),

        Rule(
            rule_id="R012",
            title="Rate Limit 초과",
            score=0.20,
            predicate=lambda logs: _any_message_regex(_RATE_LIMIT_RE, logs),
            evidence_builder=lambda logs: (
                "로그에 rate limit / too many requests / throttle 키워드가 포함됨"
            ),
            causes=[
                "API 호출 빈도 초과",
                "요청 쿼터 한도 도달",
                "DDoS 또는 비정상 트래픽",
            ],
            actions=[
                "API 호출 패턴 및 빈도 분석",
                "Rate Limit 설정 조정 요청",
                "백오프 전략 및 캐싱 적용",
            ],
        ),

        Rule(
            rule_id="R013",
            title="애플리케이션 크래시",
            score=0.45,
            predicate=lambda logs: _any_message_regex(_CRASH_RE, logs),
            evidence_builder=lambda logs: (
                "로그에 crash / panic / segfault / fatal 키워드가 포함됨"
            ),
            causes=[
                "핸들링되지 않은 예외",
                "메모리 접근 오류",
                "심각한 버그 또는 논리 오류",
            ],
            actions=[
                "크래시 덤프 및 스택 트레이스 분석",
                "최근 코드 변경사항 롤백 검토",
                "에러 핸들링 로직 강화",
            ],
        ),

        Rule(
            rule_id="R014",
            title="서비스 재시작 감지",
            score=0.30,
            predicate=lambda logs: _any_message_regex(_RESTART_RE, logs),
            evidence_builder=lambda logs: (
                "로그에 restart / reboot / killed / terminated 키워드가 포함됨"
            ),
            causes=[
                "헬스체크 실패로 인한 자동 재시작",
                "리소스 부족으로 인한 강제 종료",
                "수동 재시작 또는 배포",
            ],
            actions=[
                "재시작 직전 로그 및 메트릭 확인",
                "헬스체크 설정 및 임계값 검토",
                "리소스 할당 및 안정성 점검",
            ],
        ),

        Rule(
            rule_id="R015",
            title="SSL/TLS 인증서 문제",
            score=0.30,
            predicate=lambda logs: (
                    _any_message_regex(_SSL_RE, logs) and
                    (_any_level(LogLevel.ERROR, logs) or _has_warn_level(logs))
            ),
            evidence_builder=lambda logs: (
                "로그에 SSL/TLS/certificate 관련 키워드와 에러가 함께 포함됨"
            ),
            causes=[
                "인증서 만료",
                "인증서 체인 불일치",
                "자체 서명 인증서 신뢰 문제",
            ],
            actions=[
                "인증서 유효기간 확인",
                "인증서 체인 및 중간 인증서 검증",
                "클라이언트 truststore 설정 확인",
            ],
        ),

        Rule(
            rule_id="R016",
            title="권한 거부 오류",
            score=0.25,
            predicate=lambda logs: _any_message_regex(_PERMISSION_RE, logs),
            evidence_builder=lambda logs: (
                "로그에 permission denied / EACCES / access denied 키워드가 포함됨"
            ),
            causes=[
                "파일 또는 디렉토리 권한 부족",
                "실행 권한 미설정",
                "사용자/그룹 권한 불일치",
            ],
            actions=[
                "파일 및 디렉토리 권한 확인 (ls -la)",
                "프로세스 실행 사용자 확인",
                "필요 시 chmod/chown으로 권한 수정",
            ],
        ),

        Rule(
            rule_id="R017",
            title="4xx 클라이언트 에러 패턴",
            score=0.15,
            predicate=lambda logs: _count_matching_logs(_4XX_RE, logs) >= 3,
            evidence_builder=lambda logs: (
                f"로그에 4xx 상태 코드가 {_count_matching_logs(_4XX_RE, logs)}회 이상 반복됨"
            ),
            causes=[
                "잘못된 요청 파라미터",
                "존재하지 않는 리소스 접근",
                "클라이언트 측 버그",
            ],
            actions=[
                "요청 페이로드 및 파라미터 검증",
                "API 문서와 실제 구현 일치 확인",
                "클라이언트 코드 검토",
            ],
        ),

        Rule(
            rule_id="R018",
            title="WARN 레벨 로그 다수 존재",
            score=0.15,
            predicate=lambda logs: sum(1 for log in logs if log.level == LogLevel.WARN) >= 3,
            evidence_builder=lambda logs: (
                f"level=WARN 로그가 {sum(1 for log in logs if log.level == LogLevel.WARN)}건 발생함"
            ),
            causes=[
                "잠재적 문제 상황 발생",
                "설정 또는 리소스 관련 경고",
            ],
            actions=[
                "WARN 로그 내용 상세 검토",
                "반복되는 경고 패턴 분석",
                "예방적 조치 수행",
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
    if count >= 5:
        return 0.20
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

    # 타임아웃 + 5xx 조합
    if {"R001", "R004"} <= rule_ids:
        bonus += 0.15

    # 타임아웃 + ERROR 조합
    if {"R001", "R005"} <= rule_ids:
        bonus += 0.10

    # 연결실패 + DNS 조합
    if {"R002", "R003"} <= rule_ids:
        bonus += 0.10

    # OOM + 크래시 조합
    if {"R007", "R013"} <= rule_ids:
        bonus += 0.15

    # DB 오류 + 타임아웃 조합
    if {"R008", "R001"} <= rule_ids:
        bonus += 0.12

    # 디스크 부족 + 크래시 조합
    if {"R009", "R013"} <= rule_ids:
        bonus += 0.12

    # CPU 과부하 + 타임아웃 조합
    if {"R010", "R001"} <= rule_ids:
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
        "ruleset_version": "v2.0",
        "confidence": round(confidence, 2),
        "confidence_level": confidence_level(confidence),
        "summary": build_rule_summary(matches),
        "suspected_causes": causes,
        "recommended_actions": actions,
        "matched_rules": matched_rules,
    }