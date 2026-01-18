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
    # SINGLE RULE - NETWORK (MEDIUM)
    # ======================
    {
        "id": "TC-004",
        "description": "timeout only",
        "logs": [
            Log(source="gateway", level="ERROR", message="Request timed out after 30s"),
        ],
        "expected_rules": {"R001", "R005"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-005",
        "description": "connection refused only",
        "logs": [
            Log(source="api", level="ERROR", message="connection refused"),
        ],
        "expected_rules": {"R002", "R005"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-006",
        "description": "dns error only",
        "logs": [
            Log(source="worker", level="ERROR", message="ENOTFOUND api.internal"),
        ],
        "expected_rules": {"R003", "R005"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-007",
        "description": "5xx only",
        "logs": [
            Log(source="gateway", level="ERROR", message="502 Bad Gateway"),
        ],
        "expected_rules": {"R004", "R005"},
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
    # MEMORY / RESOURCE
    # ======================
    {
        "id": "TC-009",
        "description": "out of memory",
        "logs": [
            Log(source="app", level="ERROR", message="java.lang.OutOfMemoryError: Java heap space"),
        ],
        "expected_rules": {"R007", "R005"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-010",
        "description": "disk full",
        "logs": [
            Log(source="storage", level="ERROR", message="no space left on device"),
        ],
        "expected_rules": {"R008", "R005"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-011",
        "description": "thread pool exhausted",
        "logs": [
            Log(source="worker", level="ERROR", message="RejectedExecutionException: thread pool exhausted"),
        ],
        "expected_rules": {"R020", "R005"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-012",
        "description": "file descriptor limit",
        "logs": [
            Log(source="system", level="ERROR", message="too many open files"),
        ],
        "expected_rules": {"R022", "R005"},
        "expected_confidence_level": "MEDIUM",
    },

    # ======================
    # DATABASE
    # ======================
    {
        "id": "TC-013",
        "description": "database deadlock",
        "logs": [
            Log(source="db", level="ERROR", message="Deadlock found when trying to get lock"),
        ],
        "expected_rules": {"R009", "R005"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-014",
        "description": "connection pool exhausted",
        "logs": [
            Log(source="db", level="ERROR", message="could not get connection from pool"),
        ],
        "expected_rules": {"R010", "R005"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-015",
        "description": "slow query",
        "logs": [
            Log(source="db", level="WARN", message="slow query detected: execution time 15.3s"),
        ],
        "expected_rules": {"R011"},
        "expected_confidence_level": "LOW",
    },
    {
        "id": "TC-016",
        "description": "transaction rollback",
        "logs": [
            Log(source="db", level="ERROR", message="transaction rolled back due to constraint violation"),
        ],
        "expected_rules": {"R025", "R005"},
        "expected_confidence_level": "MEDIUM",
    },

    # ======================
    # SECURITY / AUTH
    # ======================
    {
        "id": "TC-017",
        "description": "authentication failure",
        "logs": [
            Log(source="auth", level="ERROR", message="authentication failed: invalid credentials"),
        ],
        "expected_rules": {"R012", "R005"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-018",
        "description": "rate limit exceeded",
        "logs": [
            Log(source="api", level="WARN", message="429 Too Many Requests: rate limit exceeded"),
        ],
        "expected_rules": {"R013"},
        "expected_confidence_level": "LOW",
    },
    {
        "id": "TC-019",
        "description": "certificate expired",
        "logs": [
            Log(source="https", level="ERROR", message="SSL certificate has expired"),
        ],
        "expected_rules": {"R019", "R005"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-020",
        "description": "permission denied",
        "logs": [
            Log(source="file", level="ERROR", message="permission denied: cannot write to /var/log"),
        ],
        "expected_rules": {"R027", "R005"},
        "expected_confidence_level": "MEDIUM",
    },

    # ======================
    # APPLICATION ERRORS
    # ======================
    {
        "id": "TC-021",
        "description": "null pointer exception",
        "logs": [
            Log(source="app", level="ERROR", message="NullPointerException at UserService.java:45"),
        ],
        "expected_rules": {"R014", "R005"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-022",
        "description": "serialization error",
        "logs": [
            Log(source="api", level="ERROR", message="JsonParseException: cannot deserialize response"),
        ],
        "expected_rules": {"R015", "R005"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-023",
        "description": "config missing",
        "logs": [
            Log(source="app", level="ERROR", message="configuration missing: DATABASE_URL not found"),
        ],
        "expected_rules": {"R016", "R005"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-024",
        "description": "class not found",
        "logs": [
            Log(source="app", level="ERROR", message="ClassNotFoundException: com.example.Service"),
        ],
        "expected_rules": {"R023", "R005"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-025",
        "description": "dependency version conflict",
        "logs": [
            Log(source="build", level="ERROR", message="version conflict: requires lombok 1.18 but found 1.16"),
        ],
        "expected_rules": {"R024", "R005"},
        "expected_confidence_level": "MEDIUM",
    },

    # ======================
    # INFRASTRUCTURE
    # ======================
    {
        "id": "TC-026",
        "description": "container restart loop",
        "logs": [
            Log(source="k8s", level="ERROR", message="pod app-deployment-xyz is in CrashLoopBackOff"),
        ],
        "expected_rules": {"R017", "R005"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-027",
        "description": "health check failure",
        "logs": [
            Log(source="k8s", level="WARN", message="liveness probe failed: HTTP 503"),
        ],
        "expected_rules": {"R018"},
        "expected_confidence_level": "LOW",
    },
    {
        "id": "TC-028",
        "description": "queue overflow",
        "logs": [
            Log(source="mq", level="ERROR", message="queue full: message dropped"),
        ],
        "expected_rules": {"R021", "R005"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-029",
        "description": "network partition",
        "logs": [
            Log(source="cluster", level="ERROR", message="network partition detected: quorum lost"),
        ],
        "expected_rules": {"R028", "R005"},
        "expected_confidence_level": "HIGH",
    },

    # ======================
    # REPEATED SOURCE
    # ======================
    {
        "id": "TC-030",
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
        "id": "TC-031",
        "description": "timeout + error",
        "logs": [
            Log(source="gateway", level="ERROR", message="timeout"),
            Log(source="gateway", level="ERROR", message="internal error"),
        ],
        "expected_rules": {"R001", "R005"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-032",
        "description": "timeout + 5xx",
        "logs": [
            Log(source="gateway", level="ERROR", message="timed out"),
            Log(source="gateway", level="ERROR", message="504 Gateway Timeout"),
        ],
        "expected_rules": {"R001", "R004", "R005"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-033",
        "description": "dns + connection refused",
        "logs": [
            Log(source="api", level="ERROR", message="ENOTFOUND db.internal"),
            Log(source="api", level="ERROR", message="connection refused"),
        ],
        "expected_rules": {"R002", "R003", "R005"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-034",
        "description": "oom + restart loop",
        "logs": [
            Log(source="k8s", level="ERROR", message="OutOfMemoryError"),
            Log(source="k8s", level="ERROR", message="container restarting"),
        ],
        "expected_rules": {"R007", "R017", "R005"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-035",
        "description": "deadlock + connection pool",
        "logs": [
            Log(source="db", level="ERROR", message="deadlock detected"),
            Log(source="db", level="ERROR", message="connection pool exhausted"),
        ],
        "expected_rules": {"R009", "R010", "R005"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-036",
        "description": "auth failure + rate limit",
        "logs": [
            Log(source="api", level="ERROR", message="authentication failed"),
            Log(source="api", level="WARN", message="rate limit exceeded"),
        ],
        "expected_rules": {"R012", "R013", "R005"},
        "expected_confidence_level": "HIGH",
    },

    # ======================
    # MULTI RULE (HIGH)
    # ======================
    {
        "id": "TC-037",
        "description": "timeout + 5xx + error",
        "logs": [
            Log(source="gateway", level="ERROR", message="timeout"),
            Log(source="gateway", level="ERROR", message="502 Bad Gateway"),
            Log(source="gateway", level="ERROR", message="unexpected error"),
        ],
        "expected_rules": {"R001", "R004", "R005"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-038",
        "description": "full stack failure",
        "logs": [
            Log(source="gateway", level="ERROR", message="connection refused"),
            Log(source="db", level="ERROR", message="deadlock"),
            Log(source="app", level="ERROR", message="OutOfMemoryError"),
            Log(source="k8s", level="ERROR", message="CrashLoopBackOff"),
        ],
        "expected_rules": {"R002", "R009", "R007", "R017", "R005"},
        "expected_confidence_level": "HIGH",
    },

    # ======================
    # EDGE / NOISE CASES
    # ======================
    {
        "id": "TC-039",
        "description": "info spam",
        "logs": [
            Log(source="cron", level="INFO", message="job finished") for _ in range(10)
        ],
        "expected_rules": set(),
        "expected_confidence_level": "LOW",
    },
    {
        "id": "TC-040",
        "description": "mixed info and one error",
        "logs": [
            Log(source="app", level="INFO", message="started"),
            Log(source="app", level="ERROR", message="NullPointerException"),
        ],
        "expected_rules": {"R014", "R005"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-041",
        "description": "cache miss benign",
        "logs": [
            Log(source="cache", level="INFO", message="cache miss for key user:123"),
        ],
        "expected_rules": set(),
        "expected_confidence_level": "LOW",
    },
    {
        "id": "TC-042",
        "description": "encoding warning",
        "logs": [
            Log(source="parser", level="WARN", message="UnicodeDecodeError: invalid UTF-8 sequence"),
        ],
        "expected_rules": {"R026"},
        "expected_confidence_level": "LOW",
    },

    # ======================
    # COMPLEX SCENARIOS
    # ======================
    {
        "id": "TC-043",
        "description": "cascading timeout chain",
        "logs": [
            Log(source="frontend", level="ERROR", message="API timeout after 5s"),
            Log(source="backend", level="ERROR", message="DB connection timeout"),
            Log(source="db", level="ERROR", message="slow query execution time exceeded"),
        ],
        "expected_rules": {"R001", "R011", "R005"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-044",
        "description": "security breach pattern",
        "logs": [
            Log(source="auth", level="ERROR", message="authentication failed") for _ in range(5)
        ] + [
            Log(source="api", level="WARN", message="rate limit exceeded"),
        ],
        "expected_rules": {"R012", "R013", "R005", "R006"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-045",
        "description": "gradual resource exhaustion",
        "logs": [
            Log(source="app", level="WARN", message="memory usage 85%"),
            Log(source="app", level="ERROR", message="thread pool exhausted"),
            Log(source="app", level="ERROR", message="OutOfMemoryError"),
        ],
        "expected_rules": {"R007", "R020", "R005"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-046",
        "description": "config deployment issue",
        "logs": [
            Log(source="deploy", level="ERROR", message="configuration missing: API_KEY"),
            Log(source="app", level="ERROR", message="authentication failed"),
            Log(source="k8s", level="ERROR", message="readiness probe failed"),
        ],
        "expected_rules": {"R016", "R012", "R018", "R005"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-047",
        "description": "network infrastructure issue",
        "logs": [
            Log(source="api", level="ERROR", message="connection refused"),
            Log(source="api", level="ERROR", message="ENOTFOUND service.internal"),
            Log(source="api", level="ERROR", message="timeout"),
            Log(source="lb", level="ERROR", message="503 Service Unavailable"),
        ],
        "expected_rules": {"R001", "R002", "R003", "R004", "R005"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-048",
        "description": "database saturation",
        "logs": [
            Log(source="db", level="WARN", message="slow query: 12s"),
            Log(source="db", level="ERROR", message="connection pool exhausted"),
            Log(source="db", level="ERROR", message="lock wait timeout"),
            Log(source="api", level="ERROR", message="database timeout"),
        ],
        "expected_rules": {"R001", "R010", "R011", "R005"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-049",
        "description": "certificate rotation failure",
        "logs": [
            Log(source="nginx", level="ERROR", message="SSL certificate expired"),
            Log(source="api", level="ERROR", message="TLS handshake failure"),
            Log(source="client", level="ERROR", message="connection refused"),
        ],
        "expected_rules": {"R002", "R019", "R005"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-050",
        "description": "api version incompatibility",
        "logs": [
            Log(source="client", level="ERROR", message="API version mismatch: expected v2, got v1"),
            Log(source="api", level="ERROR", message="cannot deserialize request"),
        ],
        "expected_rules": {"R015", "R030", "R005"},
        "expected_confidence_level": "HIGH",
    },

    # ======================
    # SPECIFIC TECHNOLOGY PATTERNS
    # ======================
    {
        "id": "TC-051",
        "description": "kubernetes pod eviction",
        "logs": [
            Log(source="k8s", level="WARN", message="pod evicted due to node pressure"),
            Log(source="k8s", level="ERROR", message="OOMKilled"),
        ],
        "expected_rules": {"R007", "R017", "R005"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-052",
        "description": "redis connection issue",
        "logs": [
            Log(source="redis", level="ERROR", message="connection refused"),
            Log(source="cache", level="ERROR", message="cache miss"),
        ],
        "expected_rules": {"R002", "R005"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-053",
        "description": "rabbitmq queue overflow",
        "logs": [
            Log(source="rabbitmq", level="ERROR", message="queue overflow: messages dropped"),
            Log(source="consumer", level="WARN", message="message processing delayed"),
        ],
        "expected_rules": {"R021", "R005"},
        "expected_confidence_level": "MEDIUM",
    },
    {
        "id": "TC-054",
        "description": "elasticsearch cluster red",
        "logs": [
            Log(source="es", level="ERROR", message="cluster health is RED"),
            Log(source="es", level="ERROR", message="shard allocation failed"),
        ],
        "expected_rules": {"R005"},
        "expected_confidence_level": "LOW",
    },
    {
        "id": "TC-055",
        "description": "kafka consumer lag",
        "logs": [
            Log(source="kafka", level="WARN", message="consumer lag increasing: 10000 messages behind"),
        ],
        "expected_rules": set(),
        "expected_confidence_level": "LOW",
    },

    # ======================
    # FALSE POSITIVE TESTS
    # ======================
    {
        "id": "TC-056",
        "description": "intentional retry mechanism",
        "logs": [
            Log(source="worker", level="INFO", message="retry attempt 1/3"),
            Log(source="worker", level="INFO", message="retry attempt 2/3"),
            Log(source="worker", level="INFO", message="operation succeeded"),
        ],
        "expected_rules": set(),
        "expected_confidence_level": "LOW",
    },
    {
        "id": "TC-057",
        "description": "graceful shutdown",
        "logs": [
            Log(source="app", level="INFO", message="SIGTERM received, shutting down gracefully"),
            Log(source="app", level="INFO", message="active connections: 0"),
        ],
        "expected_rules": set(),
        "expected_confidence_level": "LOW",
    },
    {
        "id": "TC-058",
        "description": "expected 404 not found",
        "logs": [
            Log(source="api", level="INFO", message="404 Not Found: /api/user/99999"),
        ],
        "expected_rules": set(),
        "expected_confidence_level": "LOW",
    },

    # ======================
    # TIME-BASED PATTERNS (future enhancement)
    # ======================
    {
        "id": "TC-059",
        "description": "gradual memory leak indication",
        "logs": [
            Log(source="monitor", level="WARN", message="heap usage 70%"),
            Log(source="monitor", level="WARN", message="heap usage 80%"),
            Log(source="monitor", level="ERROR", message="heap usage 95%"),
            Log(source="app", level="ERROR", message="OutOfMemoryError"),
        ],
        "expected_rules": {"R007", "R005"},
        "expected_confidence_level": "HIGH",
    },
    {
        "id": "TC-060",
        "description": "intermittent network issue",
        "logs": [
            Log(source="api", level="ERROR", message="timeout"),
            Log(source="api", level="INFO", message="request succeeded"),
            Log(source="api", level="ERROR", message="timeout"),
        ],
        "expected_rules": {"R001", "R005"},
        "expected_confidence_level": "MEDIUM",
    },

]