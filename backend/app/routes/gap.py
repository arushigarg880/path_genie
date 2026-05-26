# routes/gap.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.dependencies import get_current_user
from app.services.gap_service import get_skill_gap_for_user
from app.schemas.gap import SkillGapResponse
router = APIRouter(prefix="/gap", tags=["Skill Gap"])

# WHY get_db here?
# Each request gets its own database connection.
# When the request finishes, the connection closes automatically.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("")
def get_skill_gap(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the weighted skill gap for the user's active career.
    Splits missing skills into: critical, important, supplementary.
    """
    result = get_skill_gap_for_user(
        user_id=current_user.id,
        db=db
    )
    return {
        "success": True,
        "message": "Skill gap analysis complete",
        "data": result
    }