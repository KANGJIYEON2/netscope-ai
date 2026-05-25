"""Seed Netscope-AI DB with demo tenants, users, projects, logs, analyses.

Run inside the backend container (WORKDIR=/src/backend, PYTHONPATH=/src/backend):
    python -m scripts.seed              # idempotent-ish: skips existing demo emails
    python -m scripts.seed --reset      # wipe all tenant data first

Each demo user lives in their own tenant. Logging in as one user shows only
that tenant's projects/logs/analyses — that is the "각각 다른 작업자/근로자"
isolation the system enforces.
"""
from __future__ import annotations

import argparse
import random
import uuid
from datetime import datetime, timedelta, UTC
from typing import List, Tuple

from src.db.init import init_db
from src.db.base import Base
from src.db.session import SessionLocal, engine
from src.core.security import hash_password
from src.model.User import User
from src.model.Tenant import Tenant
from src.model.Project import Project
from src.model.log import Log
from src.model.analysis_result import AnalysisResult
from src.model.weekly_report import WeeklyReport
from src.model.refresh_token import RefreshToken
from src.schemas.enums import LogLevel, SeverityLevel


# ---------------------------------------------------------------------------
# Demo accounts
# ---------------------------------------------------------------------------

DEMO_USERS = [
    {
        "email": "alice@demo.io",
        "password": "Demo1234!",
        "tenant_name": "Alice Co.",
        "projects": [
            ("gateway-prod", "timeout_5xx"),
            ("auth-service", "auth_errors"),
        ],
    },
    {
        "email": "bob@demo.io",
        "password": "Demo1234!",
        "tenant_name": "Bob Industries",
        "projects": [
            ("billing-api", "db_connection"),
            ("worker-queue", "mixed"),
        ],
    },
    {
        "email": "carol@demo.io",
        "password": "Demo1234!",
        "tenant_name": "Carol Labs",
        "projects": [
            ("edge-cdn", "dns"),
            ("checkout-flow", "five_xx"),
        ],
    },
]


# (source, message, level) — picked per project to give each tenant a distinct flavor
LOG_LIBRARY: dict[str, List[Tuple[str, str, str]]] = {
    "timeout_5xx": [
        ("gateway", "Upstream request timed out after 30000ms (target=auth-svc)", "ERROR"),
        ("gateway", "ETIMEDOUT contacting payment-svc:8080", "ERROR"),
        ("gateway", "Received 504 Gateway Timeout from auth-svc /verify", "ERROR"),
        ("gateway", "Upstream returned 502 Bad Gateway (payment-svc)", "ERROR"),
        ("gateway", "Origin timed out, surfacing 502 to client", "ERROR"),
        ("gateway", "Routing /api/users -> auth-svc", "INFO"),
        ("gateway", "TLS handshake completed with edge-pop-2", "DEBUG"),
        ("gateway", "Health probe OK", "INFO"),
    ],
    "auth_errors": [
        ("auth-svc", "Failed to decode JWT: invalid signature", "ERROR"),
        ("auth-svc", "ETIMEDOUT during JWKS refresh", "ERROR"),
        ("auth-svc", "Unhandled exception in /login: KeyError 'email'", "ERROR"),
        ("auth-svc", "Token issued for user 81923", "INFO"),
        ("auth-svc", "Refreshed JWKS (3 keys)", "INFO"),
        ("auth-svc", "Login rate limit exceeded for 10.0.4.7", "WARN"),
    ],
    "db_connection": [
        ("worker", "ECONNREFUSED 10.0.4.12:5432 (db-primary)", "ERROR"),
        ("worker", "Connection refused by redis-master:6379", "ERROR"),
        ("db-proxy", "Connection refused to replica-2.db.internal", "ERROR"),
        ("db-proxy", "Connection reset by peer (pgbouncer-sidecar)", "WARN"),
        ("worker", "Job 4f21 timed out after 60s (queue=billing)", "WARN"),
        ("worker", "Job 8a91 completed in 412ms", "INFO"),
        ("db-proxy", "Health probe OK (replica lag 12ms)", "INFO"),
    ],
    "mixed": [
        ("worker", "Unhandled exception in BillingJob: KeyError 'amount'", "ERROR"),
        ("worker", "DNS resolution + connection refused for cache.internal", "ERROR"),
        ("worker", "Connection reset by peer (smtp.internal)", "WARN"),
        ("worker", "Queued job billing.run for user 81923", "INFO"),
        ("worker", "Job 8a91 completed in 412ms", "INFO"),
        ("worker", "Retry budget exhausted for charge.capture", "ERROR"),
    ],
    "dns": [
        ("frontend-edge", "getaddrinfo ENOTFOUND auth.internal", "ERROR"),
        ("frontend-edge", "DNS resolution failed: NXDOMAIN for queue.internal", "ERROR"),
        ("frontend-edge", "Name resolution failure for cdn-origin.local", "WARN"),
        ("search-svc", "ENOTFOUND es-cluster-3.search.local", "ERROR"),
        ("frontend-edge", "Cache HIT for /assets/main.js", "DEBUG"),
        ("frontend-edge", "Edge node healthy", "INFO"),
    ],
    "five_xx": [
        ("checkout", "Origin responded 504 Gateway Timeout for /api/search", "WARN"),
        ("checkout", "Upstream returned 503 Service Unavailable", "ERROR"),
        ("checkout", "Webhook target returned HTTP 502", "WARN"),
        ("checkout", "Downstream API responded 503 — backing off", "WARN"),
        ("checkout", "Charge captured: $12.40 USD", "INFO"),
        ("checkout", "Checkout flow completed in 1.2s", "INFO"),
    ],
}


# Pre-baked analyses per scenario — kept small but realistic so the dashboard has
# something to show without depending on engine wiring.
ANALYSIS_LIBRARY: dict[str, List[dict]] = {
    "timeout_5xx": [
        {
            "summary": "Gateway timeouts compounded with upstream 5xx — auth-svc is the likely root.",
            "severity": SeverityLevel.HIGH,
            "confidence": 0.86,
            "suspected_causes": [
                "Upstream(auth-svc) response latency over budget",
                "Gateway client timeout too tight under load",
                "Downstream 5xx surfaced as 502 at edge",
            ],
            "recommended_actions": [
                "Inspect auth-svc latency and pod health",
                "Raise gateway client timeout temporarily",
                "Correlate 5xx spikes with auth-svc deploys",
            ],
            "matched_rules": [
                "R001 Timeout 발생 (+0.35)",
                "R004 5xx 응답 감지 (+0.25)",
                "R005 ERROR 레벨 로그 존재 (+0.20)",
            ],
        },
        {
            "summary": "Sustained gateway 5xx with intermittent timeouts.",
            "severity": SeverityLevel.MEDIUM,
            "confidence": 0.62,
            "suspected_causes": [
                "Intermittent upstream failures",
                "Traffic spike exceeding gateway capacity",
            ],
            "recommended_actions": [
                "Check autoscaling thresholds on gateway tier",
                "Add circuit breaker for payment-svc",
            ],
            "matched_rules": [
                "R004 5xx 응답 감지 (+0.25)",
                "R001 Timeout 발생 (+0.35)",
            ],
        },
    ],
    "auth_errors": [
        {
            "summary": "Spike of auth-svc ERROR logs around JWT and JWKS refresh.",
            "severity": SeverityLevel.MEDIUM,
            "confidence": 0.58,
            "suspected_causes": [
                "JWKS endpoint slow or failing",
                "JWT key rotation mismatch",
            ],
            "recommended_actions": [
                "Verify JWKS endpoint availability",
                "Pin JWT key cache TTL above rotation interval",
            ],
            "matched_rules": [
                "R005 ERROR 레벨 로그 존재 (+0.20)",
                "R001 Timeout 발생 (+0.35)",
            ],
        },
    ],
    "db_connection": [
        {
            "summary": "Primary DB connection refused — worker tier blocked.",
            "severity": SeverityLevel.HIGH,
            "confidence": 0.82,
            "suspected_causes": [
                "db-primary process not listening on 5432",
                "pgbouncer-sidecar unhealthy",
                "Network policy blocking worker→DB",
            ],
            "recommended_actions": [
                "Check db-primary process and port binding",
                "Inspect pgbouncer-sidecar logs",
                "Review network policies for worker namespace",
            ],
            "matched_rules": [
                "R002 Connection 실패 (+0.35)",
                "R005 ERROR 레벨 로그 존재 (+0.20)",
            ],
        },
    ],
    "mixed": [
        {
            "summary": "Multiple unrelated worker errors — needs triage by job type.",
            "severity": SeverityLevel.MEDIUM,
            "confidence": 0.55,
            "suspected_causes": [
                "Application-level exceptions in BillingJob",
                "DNS + connection issues for internal cache",
            ],
            "recommended_actions": [
                "Group worker errors by job_type and root cause",
                "Verify internal DNS resolver",
            ],
            "matched_rules": [
                "R005 ERROR 레벨 로그 존재 (+0.20)",
                "R002 Connection 실패 (+0.35)",
                "R003 DNS 실패 (+0.25)",
            ],
        },
    ],
    "dns": [
        {
            "summary": "Internal DNS resolver returning NXDOMAIN for service hostnames.",
            "severity": SeverityLevel.HIGH,
            "confidence": 0.78,
            "suspected_causes": [
                "Internal DNS records removed or expired",
                "Resolver cache poisoning",
            ],
            "recommended_actions": [
                "Confirm A/AAAA records for internal services",
                "Flush resolver caches and re-test",
            ],
            "matched_rules": [
                "R003 DNS 실패 (+0.25)",
                "R005 ERROR 레벨 로그 존재 (+0.20)",
            ],
        },
    ],
    "five_xx": [
        {
            "summary": "Checkout sees sustained 5xx from downstream payments.",
            "severity": SeverityLevel.MEDIUM,
            "confidence": 0.63,
            "suspected_causes": [
                "Payment provider degraded",
                "Webhook receiver returning 502",
            ],
            "recommended_actions": [
                "Check provider status page",
                "Switch to backup webhook endpoint",
            ],
            "matched_rules": [
                "R004 5xx 응답 감지 (+0.25)",
            ],
        },
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_minus(seconds: int) -> datetime:
    return datetime.now(UTC) - timedelta(seconds=seconds)


def reset_all(db) -> None:
    # We drop_all + create_all because earlier compose runs may have left
    # legacy `logs`/`analysis_results` tables that lack tenant_id/project_id.
    # create_all alone is IF NOT EXISTS — it won't add new columns.
    print("[seed] dropping all tables (legacy schema cleanup)…")
    db.close()  # release session before DDL
    Base.metadata.drop_all(bind=engine)
    print("[seed] recreating tables with current schema…")
    Base.metadata.create_all(bind=engine)


def seed_user(db, rng: random.Random, spec: dict) -> dict:
    existing = db.query(User).filter(User.email == spec["email"]).first()
    if existing:
        print(f"[seed]   user {spec['email']} already exists — skipping")
        return {"email": spec["email"], "skipped": True}

    tenant_id = str(uuid.uuid4())
    db.add(Tenant(id=tenant_id, name=spec["tenant_name"]))

    user_id = str(uuid.uuid4())
    db.add(User(
        id=user_id,
        email=spec["email"],
        password_hash=hash_password(spec["password"]),
        tenant_id=tenant_id,
    ))

    now = datetime.now(UTC)
    project_summaries = []

    for project_name, scenario in spec["projects"]:
        project_id = str(uuid.uuid4())
        db.add(Project(id=project_id, tenant_id=tenant_id, name=project_name))

        # Logs (~18 per project)
        templates = LOG_LIBRARY[scenario]
        log_rows = []
        for _ in range(18):
            source, message, level_str = rng.choice(templates)
            ts = _now_minus(rng.randint(0, 7 * 24 * 3600))
            row = Log(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                project_id=project_id,
                source=source,
                source_type=rng.choice(("agent", "manual")),
                message=message,
                level=LogLevel(level_str),
                timestamp=ts,
                received_at=now,
                host=None,
            )
            db.add(row)
            log_rows.append(row)

        # Pre-baked analyses for this scenario
        for tmpl in ANALYSIS_LIBRARY[scenario]:
            db.add(AnalysisResult(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                project_id=project_id,
                summary=tmpl["summary"],
                severity=tmpl["severity"],
                confidence=tmpl["confidence"],
                suspected_causes=tmpl["suspected_causes"],
                recommended_actions=tmpl["recommended_actions"],
                matched_rules=tmpl["matched_rules"],
                signals={
                    "rule_hits": tmpl["matched_rules"],
                    "log_sample_count": len(log_rows),
                },
                strategy_used="rule",
                received_at=now - timedelta(minutes=rng.randint(5, 60)),
            ))

        project_summaries.append({"name": project_name, "logs": len(log_rows)})

    db.commit()
    print(f"[seed]   {spec['email']:>20s}  tenant={spec['tenant_name']:<18s}  projects={len(project_summaries)}")
    return {"email": spec["email"], "tenant": spec["tenant_name"], "projects": project_summaries, "skipped": False}


def main():
    parser = argparse.ArgumentParser(description="Seed Netscope-AI demo data")
    parser.add_argument("--reset", action="store_true", help="wipe all tenant data first")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed (for log selection)")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    if args.reset:
        # Drop/recreate handles schema; no need for plain init_db() first.
        reset_all(SessionLocal())
    else:
        print("[seed] ensuring schema (create_all)…")
        init_db()

    db = SessionLocal()
    try:
        results = []
        for spec in DEMO_USERS:
            results.append(seed_user(db, rng, spec))

        print("\n[seed] DONE — demo accounts (password: Demo1234!):")
        for r in results:
            if r.get("skipped"):
                continue
            print(f"    {r['email']:>20s}   tenant: {r['tenant']}")
        print()
    finally:
        db.close()


if __name__ == "__main__":
    main()
