"""Structured log parser unit tests."""
from src.ingest.parser import parse_log_line


# --- JSON ---

def test_json_basic():
    line = '{"level":"ERROR","message":"connection timeout","service":"api-gw"}'
    p = parse_log_line(line)
    assert p.format == "json"
    assert p.level == "ERROR"
    assert "timeout" in p.message
    assert p.source == "api-gw"


def test_json_with_extra_fields():
    line = '{"level":"WARN","msg":"slow query","app":"db-proxy","duration_ms":3200}'
    p = parse_log_line(line)
    assert p.format == "json"
    assert p.level == "WARN"
    assert p.source == "db-proxy"
    assert p.extra.get("duration_ms") == 3200


def test_json_missing_level():
    line = '{"message":"something happened","service":"worker"}'
    p = parse_log_line(line)
    assert p.format == "json"
    assert p.level == "INFO"  # default


# --- Key=Value ---

def test_kv_basic():
    line = 'level=ERROR message="disk full" source=storage host=node-3'
    p = parse_log_line(line)
    assert p.format == "kv"
    assert p.level == "ERROR"
    assert "disk full" in p.message
    assert p.source == "storage"
    assert p.host == "node-3"


def test_kv_unquoted():
    line = "level=WARN service=api-gw message=timeout"
    p = parse_log_line(line)
    assert p.format == "kv"
    assert p.level == "WARN"


# --- Syslog ---

def test_syslog_basic():
    line = "<134>Oct 11 22:14:15 webserver01 nginx[12345]: ERROR upstream timeout"
    p = parse_log_line(line)
    assert p.format == "syslog"
    assert p.source == "nginx"
    assert p.host == "webserver01"
    assert p.level == "ERROR"
    assert "upstream timeout" in p.message


def test_syslog_no_priority():
    line = "Oct 11 22:14:15 db01 postgres[5432]: FATAL connection refused"
    p = parse_log_line(line)
    assert p.format == "syslog"
    assert p.source == "postgres"
    assert p.level == "FATAL"


# --- Plain text ---

def test_plain_with_level():
    line = "2024-01-15 ERROR: NullPointerException in UserService"
    p = parse_log_line(line)
    assert p.format == "plain"
    assert p.level == "ERROR"


def test_plain_no_level():
    line = "request completed successfully"
    p = parse_log_line(line)
    assert p.format == "plain"
    assert p.level == "INFO"


def test_empty_line():
    p = parse_log_line("")
    assert p.message == ""
    assert p.format == "plain"


# --- Mixed batch ---

def test_parse_log_lines_mixed():
    from src.ingest.parser import parse_log_lines

    lines = [
        '{"level":"ERROR","message":"timeout"}',
        "level=WARN message=retry service=worker",
        "<134>Oct 11 22:14:15 host1 app[1]: disk full",
        "plain text ERROR log line",
    ]
    results = parse_log_lines(lines)
    assert len(results) == 4
    formats = [r.format for r in results]
    assert "json" in formats
    assert "kv" in formats
    assert "syslog" in formats
    assert "plain" in formats
