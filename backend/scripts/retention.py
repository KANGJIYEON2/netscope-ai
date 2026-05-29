"""
7-day retention cleanup job.

Deletes logs and analysis_results older than the retention period.

Usage:
    # Via Docker
    docker compose exec backend python -m scripts.retention

    # Standalone
    python -m scripts.retention --days 7 --dry-run

    # Cron (daily at 03:00)
    0 3 * * * cd /app && python -m scripts.retention
"""
import argparse
from datetime import datetime, timedelta, UTC

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import delete
from src.db.session import SessionLocal
from src.model.log import Log
from src.model.analysis_result import AnalysisResult
from src.model.weekly_report import WeeklyReport


TARGETS = [
    ("logs", Log, Log.received_at),
    ("analysis_results", AnalysisResult, AnalysisResult.received_at),
    ("weekly_reports", WeeklyReport, WeeklyReport.created_at),
]


def run_retention(*, days: int = 7, dry_run: bool = False) -> dict[str, int]:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    print(f"[retention] cutoff: {cutoff.isoformat()} ({days} days ago)")

    results: dict[str, int] = {}
    db = SessionLocal()

    try:
        for table_name, model, ts_col in TARGETS:
            stmt = delete(model).where(ts_col < cutoff)

            if dry_run:
                count = db.query(model).filter(ts_col < cutoff).count()
                print(f"[dry-run] {table_name}: {count} rows would be deleted")
            else:
                result = db.execute(stmt)
                count = result.rowcount
                print(f"[deleted] {table_name}: {count} rows")

            results[table_name] = count

        if not dry_run:
            db.commit()
            print("[retention] committed")
        else:
            print("[retention] dry-run complete, no changes made")

    except Exception as e:
        db.rollback()
        print(f"[retention] ERROR: {e}")
        raise
    finally:
        db.close()

    return results


def main():
    parser = argparse.ArgumentParser("Netscope retention cleanup")
    parser.add_argument("--days", type=int, default=7, help="Retention period in days (default: 7)")
    parser.add_argument("--dry-run", action="store_true", help="Preview deletions without executing")
    args = parser.parse_args()

    run_retention(days=args.days, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
