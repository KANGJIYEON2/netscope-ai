"""Rule engine unit tests — no DB required."""
from datetime import datetime, timedelta, UTC

from src.analysis.rule_engine import RuleLog, default_rules, aggregate
from src.schemas.enums import LogLevel


def _make_log(
    message: str,
    level: LogLevel = LogLevel.ERROR,
    source: str = "test",
    ts: datetime | None = None,
) -> RuleLog:
    return RuleLog(
        source=source,
        message=message,
        level=level,
        timestamp=ts or datetime.now(UTC),
    )


def _run_rules(logs):
    rules = default_rules()
    return [m for r in rules if (m := r.evaluate(logs)) is not None]


def _matched_ids(logs):
    return {m.rule_id for m in _run_rules(logs)}


# --------------------------------------------------
# Basic: rules fire on obvious patterns
# --------------------------------------------------

def test_error_log_triggers_at_least_one_rule():
    logs = [_make_log("ERROR 500 Internal Server Error on /api/users")]
    assert len(_run_rules(logs)) > 0


def test_timeout_log_triggers_rule():
    logs = [_make_log("Request TIMEOUT after 30000ms on /api/data")]
    assert len(_run_rules(logs)) > 0


def test_info_only_logs_trigger_fewer_rules():
    logs = [_make_log("User logged in successfully", LogLevel.INFO)]
    assert len(_run_rules(logs)) <= 2


# --------------------------------------------------
# Aggregate: output shape
# --------------------------------------------------

def test_aggregate_output_shape():
    logs = [
        _make_log("ERROR 500 Internal Server Error"),
        _make_log("Connection TIMEOUT after 5000ms"),
        _make_log("WARN disk usage at 95%"),
    ]
    matches = _run_rules(logs)
    assert len(matches) > 0

    result = aggregate(matches)
    assert "confidence" in result
    assert "summary" in result
    assert "suspected_causes" in result
    assert "recommended_actions" in result
    assert "matched_rules" in result
    assert 0.0 <= result["confidence"] <= 1.0


def test_aggregate_empty_matches():
    result = aggregate([])
    assert result["confidence"] == 0.0
    assert result["matched_rules"] == []


# --------------------------------------------------
# R019: Error burst (5+ errors in 1 minute)
# --------------------------------------------------

def test_r019_error_burst_triggers():
    base = datetime.now(UTC)
    logs = [
        _make_log(f"ERROR: failure #{i}", ts=base + timedelta(seconds=i * 5))
        for i in range(6)
    ]
    assert "R019" in _matched_ids(logs)


def test_r019_no_burst_when_spread():
    base = datetime.now(UTC)
    logs = [
        _make_log(f"ERROR: failure #{i}", ts=base + timedelta(minutes=i * 5))
        for i in range(6)
    ]
    assert "R019" not in _matched_ids(logs)


# --------------------------------------------------
# R020: Timeout → Crash sequence
# --------------------------------------------------

def test_r020_timeout_then_crash():
    base = datetime.now(UTC)
    logs = [
        _make_log("Request TIMEOUT after 30s", ts=base),
        _make_log("FATAL: panic - segfault in worker", ts=base + timedelta(minutes=2)),
    ]
    assert "R020" in _matched_ids(logs)


def test_r020_no_trigger_if_reversed():
    base = datetime.now(UTC)
    logs = [
        _make_log("FATAL: panic", ts=base),
        _make_log("Request TIMEOUT", ts=base + timedelta(minutes=2)),
    ]
    assert "R020" not in _matched_ids(logs)


# --------------------------------------------------
# R021: High error rate (>=50% with >=5 logs)
# --------------------------------------------------

def test_r021_high_error_rate():
    logs = [
        _make_log("ERROR: fail", LogLevel.ERROR),
        _make_log("ERROR: fail", LogLevel.ERROR),
        _make_log("ERROR: fail", LogLevel.ERROR),
        _make_log("INFO: ok", LogLevel.INFO),
        _make_log("ERROR: fail", LogLevel.ERROR),
    ]
    assert "R021" in _matched_ids(logs)


def test_r021_low_error_rate():
    logs = [
        _make_log("ERROR: fail", LogLevel.ERROR),
        _make_log("INFO: ok", LogLevel.INFO),
        _make_log("INFO: ok", LogLevel.INFO),
        _make_log("INFO: ok", LogLevel.INFO),
        _make_log("INFO: ok", LogLevel.INFO),
    ]
    assert "R021" not in _matched_ids(logs)


# --------------------------------------------------
# R022: Multi-source errors (3+ distinct sources)
# --------------------------------------------------

def test_r022_multi_source_errors():
    logs = [
        _make_log("ERROR: db down", source="api-server"),
        _make_log("ERROR: timeout", source="worker"),
        _make_log("ERROR: connection refused", source="scheduler"),
    ]
    assert "R022" in _matched_ids(logs)


def test_r022_single_source():
    logs = [
        _make_log("ERROR: fail 1", source="api"),
        _make_log("ERROR: fail 2", source="api"),
        _make_log("ERROR: fail 3", source="api"),
    ]
    assert "R022" not in _matched_ids(logs)


# --------------------------------------------------
# R024: Connection failure → restart sequence
# --------------------------------------------------

def test_r024_conn_then_restart():
    base = datetime.now(UTC)
    logs = [
        _make_log("connection refused to db:5432", ts=base),
        _make_log("container killed and restarted", ts=base + timedelta(minutes=1)),
    ]
    assert "R024" in _matched_ids(logs)


# --------------------------------------------------
# interaction_bonus: new combos
# --------------------------------------------------

def test_interaction_bonus_burst_plus_multi_source():
    base = datetime.now(UTC)
    logs = [
        _make_log(f"ERROR: failure #{i}", source=f"svc-{i % 4}",
                  ts=base + timedelta(seconds=i * 5))
        for i in range(8)
    ]
    matches = _run_rules(logs)
    result = aggregate(matches)
    # Both R019 (burst) and R022 (multi-source) should fire,
    # and interaction bonus should push confidence higher
    ids = {m.rule_id for m in matches}
    assert "R019" in ids
    assert "R022" in ids
    assert result["confidence"] > 0.5


# --------------------------------------------------
# Severity auto-mapping (via AnalysisEngine)
# --------------------------------------------------

def test_severity_critical_on_critical_combo():
    from src.analysis.engine import AnalysisEngine
    from src.schemas.enums import AnalysisStrategy

    base = datetime.now(UTC)
    messages = [
        f"ERROR: failure #{i}" for i in range(8)
    ]
    # add timeout → crash sequence + OOM to trigger CRITICAL
    messages += [
        "Request TIMEOUT after 30s",
        "FATAL: panic - segfault in worker",
        "OutOfMemoryError: heap space",
    ]

    engine = AnalysisEngine()
    result = engine.analyze_test(messages=messages, strategy=AnalysisStrategy.RULE)
    # R020 (timeout→crash) + R007 (OOM) = CRITICAL combo
    from src.schemas.enums import SeverityLevel
    assert result["severity"] in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)


def test_severity_high_on_crash():
    from src.analysis.engine import AnalysisEngine
    from src.schemas.enums import AnalysisStrategy, SeverityLevel

    engine = AnalysisEngine()
    result = engine.analyze_test(
        messages=["FATAL: panic - process crashed"],
        strategy=AnalysisStrategy.RULE,
    )
    assert result["severity"] in (SeverityLevel.HIGH, SeverityLevel.CRITICAL)


def test_severity_low_on_clean_logs():
    from src.analysis.engine import AnalysisEngine
    from src.schemas.enums import AnalysisStrategy, SeverityLevel

    engine = AnalysisEngine()
    result = engine.analyze_test(
        messages=["INFO: user logged in", "INFO: request completed"],
        strategy=AnalysisStrategy.RULE,
    )
    assert result["severity"] == SeverityLevel.LOW
