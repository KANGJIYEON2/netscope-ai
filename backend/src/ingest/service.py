import logging
import uuid
from datetime import datetime, UTC

from sqlalchemy.orm import Session

from src.analysis.engine import AnalysisEngine
from src.ingest.parser import parse_log_lines
from src.model.analysis_result import AnalysisResult
from src.schemas.enums import AnalysisStrategy
from src.realtime.broker import broker

logger = logging.getLogger(__name__)

# 싱글톤 구성 (hot path)
analysis_engine = AnalysisEngine()


def ingest_logs(*, db: Session, tenant_id: str, project_id: str, agent_id: str | None, raw_logs: list[str]):
    """
    Ingestion hot path:
    - Rule engine evaluation (analysis_engine 내부에서 수행)
    - Pattern mining (L0 — background collection)
    - 의미 있는 신호면 완전한 분석 결과를 저장하고 SSE로 실시간 푸시
    - No raw log persistence
    """
    # L0: Background pattern mining
    try:
        from src.learning.catalog import mine_and_upsert

        parsed = parse_log_lines(raw_logs)
        mine_and_upsert(
            db=db,
            tenant_id=tenant_id,
            messages=raw_logs,
            sources=[p.source for p in parsed],
            levels=[p.level for p in parsed],
        )
    except Exception as e:
        # Pattern mining failure must not break ingest
        logger.warning(f"Pattern mining failed (non-fatal): {e}")

    # ── 실시간: 의미 있는 신호면 분석 저장 + 이벤트 푸시 ──────────────
    analysis_id = None
    severity = None
    summary = None
    confidence = 0.0
    try:
        result = analysis_engine.analyze_test(
            messages=raw_logs,
            strategy=AnalysisStrategy.RULE,
        )
        if result.get("matched_rules"):
            analysis = AnalysisResult(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                project_id=project_id,
                summary=result["summary"],
                severity=result["severity"],
                confidence=result["confidence"],
                signals=result["signals"],
                suspected_causes=result["suspected_causes"],
                recommended_actions=result["recommended_actions"],
                matched_rules=result.get("matched_rules", []),
                report_sections=[],
                strategy_used="agent",
                received_at=datetime.now(UTC),
            )
            db.add(analysis)
            db.commit()
            analysis_id = analysis.id
            severity = result["severity"].value if hasattr(result["severity"], "value") else str(result["severity"])
            summary = result["summary"]
            confidence = result["confidence"]
    except Exception as e:
        logger.warning(f"Ingest analysis failed (non-fatal): {e}")

    # SSE publish — 분석이 만들어졌으면 analysis, 아니면 가벼운 ingest 펄스
    broker.publish({
        "type": "analysis" if analysis_id else "ingest",
        "tenant_id": tenant_id,
        "project_id": project_id,
        "analysis_id": analysis_id,
        "severity": severity,
        "summary": summary,
        "confidence": confidence,
        "log_count": len(raw_logs),
        "at": datetime.now(UTC).isoformat(),
    })
