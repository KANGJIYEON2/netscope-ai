"""
Variable masking for log template extraction.

Replaces dynamic values (numbers, UUIDs, IPs, timestamps, paths, etc.)
with placeholder tokens so that structurally identical messages collapse
into a single template.
"""
from __future__ import annotations

import re

# Order matters: more specific patterns first
_MASKS: list[tuple[re.Pattern, str]] = [
    # UUID v4
    (re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"), "<UUID>"),
    # ISO-8601 timestamps
    (re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b"), "<TS>"),
    # Unix epoch (10 or 13 digits)
    (re.compile(r"\b\d{10,13}\b"), "<TS>"),
    # IPv6 (simplified)
    (re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"), "<IP>"),
    # IPv4
    (re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?\b"), "<IP>"),
    # Email
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "<EMAIL>"),
    # File paths (before B64 to avoid false positives)
    (re.compile(r"(?:/[\w._-]+){2,}"), "<PATH>"),
    # JWT / Base64 (16+ chars)
    (re.compile(r"\b[A-Za-z0-9+/]{16,}={0,2}\b"), "<B64>"),
    # Hex strings (8+ chars)
    (re.compile(r"\b0x[0-9a-fA-F]{8,}\b"), "<HEX>"),
    # Numbers (3+ digits)
    (re.compile(r"\b\d{3,}\b"), "<NUM>"),
    # Quoted strings
    (re.compile(r'"[^"]{2,}"'), "<STR>"),
    (re.compile(r"'[^']{2,}'"), "<STR>"),
]


def mask_variables(message: str) -> str:
    """Replace dynamic values with placeholder tokens."""
    result = message
    for pattern, token in _MASKS:
        result = pattern.sub(token, result)
    return result
