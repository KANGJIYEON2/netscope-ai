"""
Pattern catalog API — L1 pattern management.

GET    /patterns              — list patterns for tenant (filterable by status)
GET    /patterns/{id}         — single pattern detail
PATCH  /patterns/{id}/label   — label a candidate pattern
PATCH  /patterns/{id}/dismiss — dismiss a pattern
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.v1.dep import get_current_context
from src.db.session import get_db
from src.model.pattern import Pattern, PatternFeedback
from src.learning.promotion import check_and_promote, check_demotion
from src.learning.weight_learner import apply_feedback_adjustment

router = APIRouter(prefix="/patterns", tags=["patterns"])


# ======================================================
# Schemas
# ======================================================

class LabelRequest(BaseModel):
    label: str
    display_name: str | None = None
    causes: list[str] = []
    actions: list[str] = []
    score_seed: float = 0.20


class FeedbackRequest(BaseModel):
    action: str  # confirm | dismiss | wrong
    analysis_id: str | None = None
    severity_shown: str | None = None


# ======================================================
# 1️⃣ 패턴 목록
# ======================================================
@router.get("")
def list_patterns(
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
    pattern_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
):
    tenant_id = ctx["tenant_id"]
    q = db.query(Pattern).filter(Pattern.tenant_id == tenant_id)

    if pattern_status:
        q = q.filter(Pattern.status == pattern_status)

    total = q.count()
    patterns = (
        q.order_by(Pattern.total_count.desc(), Pattern.last_seen.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "items": [_to_dto(p) for p in patterns],
    }


# ======================================================
# 2️⃣ 패턴 상세
# ======================================================
@router.get("/{pattern_id}")
def get_pattern(
    pattern_id: str,
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    pattern = _get_or_404(db, ctx["tenant_id"], pattern_id)
    return _to_dto(pattern)


# ======================================================
# 3️⃣ 패턴 라벨링
# ======================================================
@router.patch("/{pattern_id}/label")
def label_pattern(
    pattern_id: str,
    req: LabelRequest,
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    pattern = _get_or_404(db, ctx["tenant_id"], pattern_id)

    if req.score_seed > 0.30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="score_seed cannot exceed 0.30 (safety guard)",
        )

    pattern.label = req.label
    pattern.display_name = req.display_name
    pattern.causes = req.causes
    pattern.actions = req.actions
    pattern.score_seed = req.score_seed
    pattern.status = "labeled"

    db.commit()
    return _to_dto(pattern)


# ======================================================
# 4️⃣ 패턴 무시
# ======================================================
@router.patch("/{pattern_id}/dismiss")
def dismiss_pattern(
    pattern_id: str,
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    pattern = _get_or_404(db, ctx["tenant_id"], pattern_id)
    pattern.status = "dismissed"
    db.commit()
    return _to_dto(pattern)


# ======================================================
# 5️⃣ 패턴 피드백 (L3)
# ======================================================
@router.post("/{pattern_id}/feedback")
def submit_feedback(
    pattern_id: str,
    req: FeedbackRequest,
    ctx: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    if req.action not in ("confirm", "dismiss", "wrong"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="action must be one of: confirm, dismiss, wrong",
        )

    pattern = _get_or_404(db, ctx["tenant_id"], pattern_id)

    # Record feedback
    feedback = PatternFeedback(
        tenant_id=ctx["tenant_id"],
        pattern_id=pattern_id,
        analysis_id=req.analysis_id,
        action=req.action,
        user_id=ctx["user_id"],
        severity_shown=req.severity_shown,
    )
    db.add(feedback)

    # Update counters
    if req.action == "confirm":
        pattern.confirm_count += 1
    elif req.action in ("dismiss", "wrong"):
        pattern.dismiss_count += 1

    db.commit()

    # L4: Apply score adjustment
    apply_feedback_adjustment(
        db=db,
        pattern=pattern,
        action=req.action,
        user_id=ctx.get("user_id"),
    )

    # L3: Check auto-promotion / demotion
    check_and_promote(db, pattern)
    check_demotion(db, pattern)

    return _to_dto(pattern)


# ======================================================
# Helpers
# ======================================================

def _get_or_404(db: Session, tenant_id: str, pattern_id: str) -> Pattern:
    pattern = (
        db.query(Pattern)
        .filter(Pattern.id == pattern_id, Pattern.tenant_id == tenant_id)
        .first()
    )
    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pattern not found",
        )
    return pattern


def _to_dto(p: Pattern) -> dict:
    return {
        "id": p.id,
        "template": p.template,
        "sample": p.sample,
        "total_count": p.total_count,
        "first_seen": p.first_seen.isoformat() if p.first_seen else None,
        "last_seen": p.last_seen.isoformat() if p.last_seen else None,
        "sources": p.sources,
        "level_dist": p.level_dist,
        "hourly_dist": p.hourly_dist,
        "status": p.status,
        "label": p.label,
        "display_name": p.display_name,
        "causes": p.causes,
        "actions": p.actions,
        "score_seed": p.score_seed,
        "score_adjust": p.score_adjust,
        "confirm_count": p.confirm_count,
        "dismiss_count": p.dismiss_count,
    }
