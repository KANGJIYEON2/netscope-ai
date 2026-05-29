"""Rule engine unit tests — no DB required."""
from datetime import datetime, UTC

from src.analysis.rule_engine import RuleLog, default_rules, aggregate
from src.schemas.enums import LogLevel


def _make_log(message: str, level: LogLevel = LogLevel.ERROR) -> RuleLog:
    return RuleLog(
        source="test",
        message=message,
        level=level,
        timestamp=datetime.now(UTC),
    )


# --------------------------------------------------
# Basic: rules fire on obvious patterns
# --------------------------------------------------

def test_error_log_triggers_at_least_one_rule():
    logs = [_make_log("ERROR 500 Internal Server Error on /api/users")]
    rules = default_rules()
    matches = [m for r in rules if (m := r.evaluate(logs)) is not None]
    assert len(matches) > 0, "At least one rule should match a 500 error log"


def test_timeout_log_triggers_rule():
    logs = [_make_log("Request TIMEOUT after 30000ms on /api/data")]
    rules = default_rules()
    matches = [m for r in rules if (m := r.evaluate(logs)) is not None]
    assert len(matches) > 0, "Timeout pattern should trigger at least one rule"


def test_info_only_logs_trigger_fewer_rules():
    logs = [_make_log("User logged in successfully", LogLevel.INFO)]
    rules = default_rules()
    matches = [m for r in rules if (m := r.evaluate(logs)) is not None]
    # INFO-only logs should trigger far fewer (possibly zero) rules
    assert len(matches) <= 2


# --------------------------------------------------
# Aggregate: output shape
# --------------------------------------------------

def test_aggregate_output_shape():
    logs = [
        _make_log("ERROR 500 Internal Server Error"),
        _make_log("Connection TIMEOUT after 5000ms"),
        _make_log("WARN disk usage at 95%"),
    ]
    rules = default_rules()
    matches = [m for r in rules if (m := r.evaluate(logs)) is not None]
    assert len(matches) > 0, "Should have matches for aggregate test"

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
