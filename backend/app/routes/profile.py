from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.profile import ProfileUpdate, ProfileResponse, SkillAddRequest, UserSkillResponse
from app.services import profile_service

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("")
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = profile_service.get_profile(db, current_user)
    return {
        "success": True,
        "message": "Profile retrieved",
        "data": profile
    }


@router.put("")
def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        updated = profile_service.update_profile(db, current_user, data)
        return {
            "success": True,
            "message": "Profile updated. Please regenerate your roadmap." if updated.regeneration_needed else "Profile updated.",
            "data": updated
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/skills")
def add_skill(
    data: SkillAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        skill = profile_service.add_skill(db, current_user, data.skill_id, data.proficiency)
        return {
            "success": True,
            "message": "Skill added successfully",
            "data": skill
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/skills")
def get_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    skills = profile_service.get_skills(db, current_user)
    return {
        "success": True,
        "message": "Skills retrieved",
        "data": skills
    }


@router.delete("/skills/{skill_id}")
def remove_skill(
    skill_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        profile_service.remove_skill(db, current_user, skill_id)
        return {
            "success": True,
            "message": "Skill removed successfully",
            "data": None
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))