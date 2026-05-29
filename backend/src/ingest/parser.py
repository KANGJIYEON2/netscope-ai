"""
Structured log parser — extracts fields from raw log lines.

Supports:
  1. JSON logs:       {"level":"ERROR","message":"timeout","service":"api"}
  2. Key=Value logs:  level=ERROR message="timeout occurred" service=api
  3. Syslog (RFC 3164): <134>Oct 11 22:14:15 server01 app[12345]: connection refused
  4. Plain text:      fallback — returns raw message with inferred level
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class ParsedLog:
    """Normalized output of the parser."""
    message: str
    level: str = "INFO"
    source: str = "unknown"
    timestamp: str | None = None
    host: str | None = None
    extra: dict = field(default_factory=dict)
    format: str = "plain"  # json | kv | syslog | plain


# --- JSON parser ---

def _try_json(line: str) -> ParsedLog | None:
    stripped = line.strip()
    if not stripped.startswith("{"):
        return None
    try:
        obj = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        return None

    if not isinstance(obj, dict):
        return None

    message = (
        obj.get("message")
        or obj.get("msg")
        or obj.get("log")
        or obj.get("text")
        or stripped
    )
    level = (
        obj.get("level")
        or obj.get("severity")
        or obj.get("loglevel")
        or "INFO"
    )
    source = (
        obj.get("source")
        or obj.get("service")
        or obj.get("app")
        or obj.get("logger")
        or "unknown"
    )
    timestamp = obj.get("timestamp") or obj.get("time") or obj.get("ts")
    host = obj.get("host") or obj.get("hostname")

    known_keys = {
        "message", "msg", "log", "text",
        "level", "severity", "loglevel",
        "source", "service", "app", "logger",
        "timestamp", "time", "ts",
        "host", "hostname",
    }
    extra = {k: v for k, v in obj.items() if k not in known_keys}

    return ParsedLog(
        message=str(message),
        level=str(level).upper(),
        source=str(source),
        timestamp=str(timestamp) if timestamp else None,
        host=str(host) if host else None,
        extra=extra,
        format="json",
    )


# --- Key=Value parser ---

_KV_RE = re.compile(
    r'(\w+)\s*=\s*(?:"([^"]*?)"|(\S+))'
)


def _try_kv(line: str) -> ParsedLog | None:
    pairs = _KV_RE.findall(line)
    if len(pairs) < 2:
        return None

    kv = {k.lower(): (v1 or v2) for k, v1, v2 in pairs}

    message = kv.get("message") or kv.get("msg") or line
    level = kv.get("level") or kv.get("severity") or "INFO"
    source = kv.get("source") or kv.get("service") or "unknown"
    timestamp = kv.get("timestamp") or kv.get("time")
    host = kv.get("host") or kv.get("hostname")

    known_keys = {
        "message", "msg", "level", "severity",
        "source", "service", "timestamp", "time",
        "host", "hostname",
    }
    extra = {k: v for k, v in kv.items() if k not in known_keys}

    return ParsedLog(
        message=str(message),
        level=str(level).upper(),
        source=str(source),
        timestamp=timestamp,
        host=host,
        extra=extra,
        format="kv",
    )


# --- Syslog (RFC 3164) parser ---

_SYSLOG_RE = re.compile(
    r"^(?:<\d+>)?"                          # optional priority
    r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"  # timestamp
    r"(\S+)\s+"                             # hostname
    r"(\S+?)(?:\[\d+\])?:\s+"              # app[pid]:
    r"(.+)$"                                # message
)

_LEVEL_RE = re.compile(r"\b(ERROR|WARN|INFO|DEBUG|FATAL|CRITICAL)\b", re.IGNORECASE)


def _try_syslog(line: str) -> ParsedLog | None:
    m = _SYSLOG_RE.match(line.strip())
    if not m:
        return None

    ts_str, host, app, message = m.groups()

    level_m = _LEVEL_RE.search(message)
    level = level_m.group(1).upper() if level_m else "INFO"

    return ParsedLog(
        message=message,
        level=level,
        source=app,
        timestamp=ts_str,
        host=host,
        format="syslog",
    )


# --- Plain text fallback ---

def _parse_plain(line: str) -> ParsedLog:
    level_m = _LEVEL_RE.search(line)
    level = level_m.group(1).upper() if level_m else "INFO"

    return ParsedLog(
        message=line.strip(),
        level=level,
        format="plain",
    )


# --- Public API ---

def parse_log_line(line: str) -> ParsedLog:
    """Parse a single raw log line, trying formats in priority order."""
    if not line or not line.strip():
        return ParsedLog(message="", format="plain")

    return (
        _try_json(line)
        or _try_syslog(line)
        or _try_kv(line)
        or _parse_plain(line)
    )


def parse_log_lines(lines: list[str]) -> list[ParsedLog]:
    """Parse multiple raw log lines."""
    return [parse_log_line(line) for line in lines]
