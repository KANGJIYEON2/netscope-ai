from src.log.models import Log

TEST_CASES = [

    # ======================
    # NO SIGNAL (LOW)
    # ======================
    {
        "id": "TC-001",
        "description": "normal info log",
        "logs": [
            Log(source="auth", level="INFO", message="User login success"),
        ],
        "expected_rules": set(),
        "expected_confidence_level": "LOW",
    },
    {
        "id": "TC-002",
        "description": "debug only",
        "logs": [
            Log(source="worker", level="DEBUG", message="heartbeat ok"),
        ],
        "expected_rules": set(),
        "expected_confidence_level": "LOW",
    },
    {
        "id": "TC-003",
        "description": "single warning",
        "logs": [
            Log(source="gateway", level="WARN", message="slow response"),
        ],
        "expected_rules": set(),
        "expected_confidence_level": "LOW",
    },

    # ======================
    # SINGLE RULE (MEDIUM)
    # ======================
    {
        "id": "TC-004",
        "description": "timeout only",
        "logs": [
            Log(source="gateway", level="ERROR", message="Request timed out after 30s"),
        ],
        "expected_rules": {"R001"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-005",
        "description": "connection refused only",
        "logs": [
            Log(source="api", level="ERROR", message="connection refused"),
        ],
        "expected_rules": {"R002"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-006",
        "description": "dns error only",
        "logs": [
            Log(source="worker", level="ERROR", message="ENOTFOUND api.internal"),
        ],
        "expected_rules": {"R003"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-007",
        "description": "5xx only",
        "logs": [
            Log(source="gateway", level="ERROR", message="502 Bad Gateway"),
        ],
        "expected_rules": {"R004"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-008",
        "description": "error level only",
        "logs": [
            Log(source="app", level="ERROR", message="Unhandled exception occurred"),
        ],
        "expected_rules": {"R005"},
        "expected_confidence_level": "LOW",
    },

    # ======================
    # REPEATED SOURCE
    # ======================
    {
        "id": "TC-009",
        "description": "log burst same source",
        "logs": [
            Log(source="worker", level="ERROR", message="retry failed") for _ in range(5)
        ],
        "expected_rules": {"R005", "R006"},
        "expected_confidence_level": "MEDIUM",
    },

    # ======================
    # DOUBLE RULE (MEDIUM~HIGH)
    # ======================
    {
        "id": "TC-010",
        "description": "timeout + error",
        "logs": [
            Log(source="gateway", level="ERROR", message="timeout"),
            Log(source="gateway", level="ERROR", message="internal error"),
        ],
        "expected_rules": {"R001", "R005"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-011",
        "description": "timeout + 5xx",
        "logs": [
            Log(source="gateway", level="ERROR", message="timed out"),
            Log(source="gateway", level="ERROR", message="504 Gateway Timeout"),
        ],
        "expected_rules": {"R001", "R004"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-012",
        "description": "dns + connection refused",
        "logs": [
            Log(source="api", level="ERROR", message="ENOTFOUND db.internal"),
            Log(source="api", level="ERROR", message="connection refused"),
        ],
        "expected_rules": {"R002", "R003"},
        "expected_confidence_level": "HIGH",
    },

    # ======================
    # MULTI RULE (HIGH)
    # ======================
    {
        "id": "TC-013",
        "description": "timeout + 5xx + error",
        "logs": [
            Log(source="gateway", level="ERROR", message="timeout"),
            Log(source="gateway", level="ERROR", message="502 Bad Gateway"),
            Log(source="gateway", level="ERROR", message="unexpected error"),
        ],
        "expected_rules": {"R001", "R004", "R005"},
        "expected_confidence_level": "HIGH",
    },

    # ======================
    # EDGE / NOISE CASES
    # ======================
    {
        "id": "TC-014",
        "description": "info spam",
        "logs": [
            Log(source="cron", level="INFO", message="job finished") for _ in range(10)
        ],
        "expected_rules": set(),
        "expected_confidence_level": "LOW",
    },
    {
        "id": "TC-015",
        "description": "mixed info and one error",
        "logs": [
            Log(source="app", level="INFO", message="started"),
            Log(source="app", level="ERROR", message="NullPointerException"),
        ],
        "expected_rules": {"R005"},
        "expected_confidence_level": "LOW",
    },

]

# ---- auto-generate remaining simple variations to reach ~50 ----
base_id = 16
for i in range(35):
    TEST_CASES.append({
        "id": f"TC-{base_id + i:03d}",
        "description": f"timeout variation {i}",
        "logs": [
            Log(source="gateway", level="ERROR", message="Request timed out"),
        ],
        "expected_rules": {"R001"},
        "expected_confidence_level": "MEDIUM",
    })
