from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.dependencies import get_current_user, require_complete_profile
from app.db.session import get_db
from app.models.user import User
from app.services import career_service

router = APIRouter(prefix="/careers", tags=["Careers"])


@router.get("")
def get_all_careers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    careers = career_service.get_all_careers(db)
    return {
        "success": True,
        "message": "Careers retrieved",
        "data": careers
    }


@router.get("/compare")
def compare_careers(
    a: UUID,
    b: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        result = career_service.compare_careers(db, current_user, a, b)
        return {
            "success": True,
            "message": "Comparison complete",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{career_id}")
def get_career(
    career_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        career = career_service.get_career_by_id(db, career_id)
        return {
            "success": True,
            "message": "Career retrieved",
            "data": career
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/select")
def select_career(
    career_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_complete_profile)
):
    try:
        career = career_service.select_career(db, current_user, career_id)
        return {
            "success": True,
            "message": "Career selected. If you had a previous roadmap, please regenerate it.",
            "data": {
                "id": str(career.id),
                "name": career.name,
                "description": career.description,
                "math_intensity": career.math_intensity,
                "coding_intensity": career.coding_intensity,
                "estimated_prep_weeks": career.estimated_prep_weeks
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))