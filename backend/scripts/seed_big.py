"""Augment the demo tenants with a LOT of backdated logs + analyses.

Unlike scripts.seed (which wipes + lays down a small fixed set), this script
ADDS bulk, time-spread data to the existing alice/bob/carol tenants so the Fleet
dashboard, trend charts, issue board and live feed all look populated.

Run inside the backend container:
    python -m scripts.seed_big                       # defaults
    python -m scripts.seed_big --analyses 30 --logs 80 --days 14
    python -m scripts.seed_big --purge               # remove previously bulk-seeded rows first

Backdating: ~70% of rows are spread across the last N days (one trend point per
day), ~30% land in the last 6 hours so the live feed / 24h KPIs stay fresh.
Bulk rows are tagged in `signals.seed='bulk'` (analyses) / source_type='bulk'
(logs) so --purge can find them.
"""
from __future__ import annotations

import argparse
import random
import uuid
from datetime import datetime, timedelta, UTC

from src.db.init import init_db
from src.db.session import SessionLocal
from src.model.User import User
from src.model.Project import Project
from src.model.log import Log
from src.model.analysis_result import AnalysisResult
from src.schemas.enums import LogLevel, SeverityLevel

DEMO_EMAILS = ["alice@demo.io", "bob@demo.io", "carol@demo.io"]

# Extra projects added per tenant (idempotent by name) so the fleet grid is full.
EXTRA_PROJECTS = {
    "alice@demo.io": ["payments-api", "notification-svc", "search-svc"],
    "bob@demo.io": ["inventory-svc", "shipping-api", "analytics-job"],
    "carol@demo.io": ["media-encoder", "recommendation-svc", "mobile-bff"],
}

# ---------------------------------------------------------------------------
# Themes — coherent (rules + summaries + causes/actions) so Recurring Issues
# and the severity board look meaningful, not random noise.
# ---------------------------------------------------------------------------
THEMES = [
    {
        "key": "timeout_5xx",
        "rules": ["R001 Timeout 발생 (+0.35)", "R004 5xx 응답 감지 (+0.25)", "R005 ERROR 레벨 로그 존재 (+0.20)"],
        "sev_weights": {"LOW": 1, "MEDIUM": 4, "HIGH": 4, "CRITICAL": 1},
        "summaries": [
            "Gateway timeouts compounded with upstream 5xx — auth-svc likely root.",
            "Sustained 504/502 from edge while upstream latency climbs.",
            "Intermittent gateway timeouts during traffic spike.",
        ],
        "causes": ["Upstream latency over budget", "Client timeout too tight under load", "Downstream 5xx surfaced as 502"],
        "actions": ["Inspect upstream pod health", "Raise gateway client timeout", "Add circuit breaker"],
        "sources": ["gateway", "edge-pop-2", "lb"],
        "logs": [
            ("gateway", "Upstream request timed out after 30000ms", "ERROR"),
            ("gateway", "Received 504 Gateway Timeout from auth-svc /verify", "ERROR"),
            ("gateway", "Upstream returned 502 Bad Gateway (payment-svc)", "ERROR"),
            ("gateway", "Routing /api/users -> auth-svc", "INFO"),
            ("gateway", "TLS handshake completed with edge-pop-2", "DEBUG"),
        ],
    },
    {
        "key": "db",
        "rules": ["R002 Connection 실패 (+0.35)", "R008 데이터베이스 관련 오류 (+0.30)", "R005 ERROR 레벨 로그 존재 (+0.20)"],
        "sev_weights": {"LOW": 1, "MEDIUM": 3, "HIGH": 5, "CRITICAL": 1},
        "summaries": [
            "Primary DB connection refused — worker tier blocked.",
            "Connection pool exhausted against db-primary.",
            "pgbouncer sidecar dropping connections under load.",
        ],
        "causes": ["db-primary not listening on 5432", "pgbouncer-sidecar unhealthy", "Network policy blocking worker→DB"],
        "actions": ["Check db-primary port binding", "Inspect pgbouncer logs", "Review worker network policy"],
        "sources": ["worker", "db-proxy", "pgbouncer"],
        "logs": [
            ("worker", "ECONNREFUSED 10.0.4.12:5432 (db-primary)", "ERROR"),
            ("db-proxy", "could not get connection from pool", "ERROR"),
            ("db-proxy", "Connection reset by peer (pgbouncer-sidecar)", "WARN"),
            ("worker", "Job 8a91 completed in 412ms", "INFO"),
        ],
    },
    {
        "key": "oom",
        "rules": ["R007 Out of Memory 감지 (+0.40)", "R017 컨테이너 재시작 루프 (+0.30)", "R005 ERROR 레벨 로그 존재 (+0.20)"],
        "sev_weights": {"LOW": 0, "MEDIUM": 2, "HIGH": 4, "CRITICAL": 4},
        "summaries": [
            "OutOfMemory followed by CrashLoopBackOff — pod restarting.",
            "Heap exhaustion crashing the worker repeatedly.",
            "OOMKilled under sustained load, restart loop active.",
        ],
        "causes": ["Memory leak accumulating heap", "Resource limits too low", "Restart loop after OOM"],
        "actions": ["Raise memory limits", "Profile heap allocations", "Add graceful shutdown"],
        "sources": ["k8s", "worker", "app"],
        "logs": [
            ("app", "java.lang.OutOfMemoryError: Java heap space", "ERROR"),
            ("k8s", "pod app-deployment-xyz is in CrashLoopBackOff", "ERROR"),
            ("k8s", "OOMKilled (memory limit 512Mi exceeded)", "ERROR"),
            ("app", "GC pause 1.8s, heap 95%", "WARN"),
        ],
    },
    {
        "key": "dns",
        "rules": ["R003 DNS 실패 (+0.25)", "R005 ERROR 레벨 로그 존재 (+0.20)"],
        "sev_weights": {"LOW": 2, "MEDIUM": 5, "HIGH": 2, "CRITICAL": 0},
        "summaries": [
            "Internal DNS returning NXDOMAIN for service hostnames.",
            "Name resolution intermittently failing for internal services.",
        ],
        "causes": ["Internal DNS records expired", "Resolver cache issue"],
        "actions": ["Confirm A/AAAA records", "Flush resolver caches"],
        "sources": ["frontend-edge", "search-svc"],
        "logs": [
            ("frontend-edge", "getaddrinfo ENOTFOUND auth.internal", "ERROR"),
            ("search-svc", "ENOTFOUND es-cluster-3.search.local", "ERROR"),
            ("frontend-edge", "Edge node healthy", "INFO"),
        ],
    },
    {
        "key": "burst",
        "rules": ["R019 에러 버스트 (+0.40)", "R021 높은 에러율 (+0.35)", "R022 다중 source 동시 에러 (+0.35)", "R005 ERROR 레벨 로그 존재 (+0.20)"],
        "sev_weights": {"LOW": 0, "MEDIUM": 2, "HIGH": 4, "CRITICAL": 3},
        "summaries": [
            "Error burst across multiple sources — fleet-wide incident.",
            "Sharp error-rate spike within a 1-minute window.",
            "Simultaneous failures across 4 services — common dependency down.",
        ],
        "causes": ["Shared dependency (DB/cache) outage", "Bad deploy fanned out", "Infra-level failure"],
        "actions": ["Check recent deploys", "Inspect shared dependencies", "Decide rollback"],
        "sources": ["gateway", "worker", "db-proxy", "cache"],
        "logs": [
            ("cache", "Connection refused by redis-master:6379", "ERROR"),
            ("worker", "Retry budget exhausted for charge.capture", "ERROR"),
            ("gateway", "5xx rate 71% over last 60s", "ERROR"),
            ("db-proxy", "lock wait timeout exceeded", "ERROR"),
        ],
    },
    {
        "key": "auth",
        "rules": ["R005 ERROR 레벨 로그 존재 (+0.20)", "R001 Timeout 발생 (+0.35)"],
        "sev_weights": {"LOW": 3, "MEDIUM": 5, "HIGH": 1, "CRITICAL": 0},
        "summaries": [
            "Spike of auth-svc errors around JWT and JWKS refresh.",
            "JWKS refresh latency causing token validation failures.",
        ],
        "causes": ["JWKS endpoint slow or failing", "JWT key rotation mismatch"],
        "actions": ["Verify JWKS availability", "Pin JWT cache TTL above rotation interval"],
        "sources": ["auth-svc"],
        "logs": [
            ("auth-svc", "Failed to decode JWT: invalid signature", "ERROR"),
            ("auth-svc", "ETIMEDOUT during JWKS refresh", "ERROR"),
            ("auth-svc", "Token issued for user 81923", "INFO"),
        ],
    },
]

SEV_CONF = {
    "LOW": (0.20, 0.44),
    "MEDIUM": (0.45, 0.74),
    "HIGH": (0.75, 0.84),
    "CRITICAL": (0.85, 0.98),
}


def weighted_severity(rng: random.Random, weights: dict[str, int]) -> str:
    keys = [k for k, w in weights.items() for _ in range(w)]
    return rng.choice(keys)


def random_when(rng: random.Random, days: int) -> datetime:
    now = datetime.now(UTC)
    if rng.random() < 0.30:
        # fresh — last 6 hours
        return now - timedelta(seconds=rng.randint(0, 6 * 3600))
    # spread across the window
    return now - timedelta(
        days=rng.randint(0, days - 1),
        seconds=rng.randint(0, 24 * 3600),
    )


def ensure_projects(db, tenant_id: str, names: list[str]) -> list[Project]:
    out = []
    for name in names:
        existing = (
            db.query(Project)
            .filter(Project.tenant_id == tenant_id, Project.name == name)
            .first()
        )
        if not existing:
            existing = Project(id=str(uuid.uuid4()), tenant_id=tenant_id, name=name)
            db.add(existing)
        out.append(existing)
    db.commit()
    return out


def purge(db) -> int:
    n1 = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.strategy_used == "bulk")
        .delete(synchronize_session=False)
    )
    n2 = (
        db.query(Log)
        .filter(Log.source_type == "bulk")
        .delete(synchronize_session=False)
    )
    db.commit()
    print(f"[seed_big] purged {n1} analyses + {n2} logs")
    return n1 + n2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--analyses", type=int, default=28, help="analyses per project")
    ap.add_argument("--logs", type=int, default=70, help="logs per project")
    ap.add_argument("--days", type=int, default=14, help="backdate window")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--purge", action="store_true", help="remove prior bulk rows first")
    args = ap.parse_args()

    init_db()
    rng = random.Random(args.seed)
    db = SessionLocal()

    try:
        if args.purge:
            purge(db)

        total_logs = total_analyses = 0

        for email in DEMO_EMAILS:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                print(f"[seed_big] {email} not found — run scripts.seed first; skipping")
                continue
            tenant_id = user.tenant_id

            # existing + extra projects
            ensure_projects(db, tenant_id, EXTRA_PROJECTS.get(email, []))
            projects = db.query(Project).filter(Project.tenant_id == tenant_id).all()

            for proj in projects:
                # logs
                for _ in range(args.logs):
                    theme = rng.choice(THEMES)
                    source, message, level = rng.choice(theme["logs"])
                    when = random_when(rng, args.days)
                    db.add(Log(
                        id=str(uuid.uuid4()),
                        tenant_id=tenant_id,
                        project_id=proj.id,
                        source=source,
                        source_type="bulk",
                        message=message,
                        level=LogLevel(level),
                        timestamp=when,
                        received_at=when,
                        host=None,
                    ))
                    total_logs += 1

                # analyses
                for _ in range(args.analyses):
                    theme = rng.choice(THEMES)
                    sev = weighted_severity(rng, theme["sev_weights"])
                    lo, hi = SEV_CONF[sev]
                    conf = round(rng.uniform(lo, hi), 2)
                    rules = theme["rules"][:]
                    rng.shuffle(rules)
                    rules = rules[: rng.randint(2, len(rules))]
                    when = random_when(rng, args.days)
                    db.add(AnalysisResult(
                        id=str(uuid.uuid4()),
                        tenant_id=tenant_id,
                        project_id=proj.id,
                        summary=rng.choice(theme["summaries"]),
                        severity=SeverityLevel(sev),
                        confidence=conf,
                        suspected_causes=rng.sample(theme["causes"], k=min(2, len(theme["causes"]))),
                        recommended_actions=rng.sample(theme["actions"], k=min(2, len(theme["actions"]))),
                        matched_rules=rules,
                        signals={"seed": "bulk", "theme": theme["key"]},
                        strategy_used="bulk",
                        received_at=when,
                    ))
                    total_analyses += 1

            db.commit()
            print(f"[seed_big] {email:>18s}  projects={len(projects)}")

        print(f"\n[seed_big] DONE — +{total_logs} logs, +{total_analyses} analyses "
              f"across {args.days}d window")
    finally:
        db.close()


if __name__ == "__main__":
    main()
