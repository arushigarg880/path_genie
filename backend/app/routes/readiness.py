# app/routes/readiness.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timezone, datetime
from app.db.session import SessionLocal
from app.core.dependencies import get_current_user
from app.models.career import UserCareer
from app.models.career import CareerSkill
from app.models.skill import Skill
from app.models.skill import UserSkill
from app.engines.readiness_engine import compute_readiness_score

router = APIRouter(prefix="/readiness", tags=["Readiness"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def get_readiness_score(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Step 1: Get active career
    active_career = db.query(UserCareer).filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()

    if not active_career:
        raise HTTPException(status_code=400, detail="No active career selected")

    # Step 2: Get all career skills with weights
    career_skills_db = db.query(CareerSkill).filter_by(
        career_id=active_career.career_id
    ).all()

    if not career_skills_db:
        raise HTTPException(status_code=404, detail="No skills found for this career")

    # Step 3: Build career_skills list for engine
    skill_ids = [str(cs.skill_id) for cs in career_skills_db]
    skill_lookup = {
        str(s.id): s for s in db.query(Skill).filter(Skill.id.in_(skill_ids)).all()
    }

    career_skills = []
    for cs in career_skills_db:
        skill = skill_lookup.get(str(cs.skill_id))
        if skill:
            career_skills.append({
                "skill_id": str(cs.skill_id),
                "importance_weight": cs.importance_weight,
                "category": skill.category
            })

    # Step 4: Get user's known skills
    user_skills_db = db.query(UserSkill).filter(
        UserSkill.user_id == current_user.id,
        UserSkill.skill_id.in_(skill_ids)
    ).all()

    user_skills = []
    for us in user_skills_db:
        user_skills.append({
            "skill_id": str(us.skill_id),
            "proficiency": us.proficiency,
            "last_practiced": us.last_practiced if us.last_practiced else date.today()
        })

    # Step 5: Compute score
    result = compute_readiness_score(career_skills, user_skills)

    return {
        "success": True,
        "message": "Readiness score computed",
        "data": {
            "overall_score": result["overall_score"],
            "category_breakdown": result["category_breakdown"],
            "needs_review_count": result["needs_review_count"],
            "skill_details": result["skill_details"]
        }
    }


@router.post("/refresh/{skill_id}")
def refresh_skill(
    skill_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Step 1: Find user's skill
    user_skill = db.query(UserSkill).filter(
        UserSkill.user_id == current_user.id,
        UserSkill.skill_id == skill_id
    ).first()

    if not user_skill:
        raise HTTPException(status_code=404, detail="Skill not found in your profile")

    # Step 2: Update last_practiced to today
    user_skill.last_practiced = date.today()
    db.commit()

    # Step 3: Recompute score immediately (FR-7.8)
    active_career = db.query(UserCareer).filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()

    if not active_career:
        return {
            "success": True,
            "message": "Skill refreshed successfully",
            "data": {"skill_id": skill_id, "last_practiced": str(date.today())}
        }

    career_skills_db = db.query(CareerSkill).filter_by(
        career_id=active_career.career_id
    ).all()

    skill_ids = [str(cs.skill_id) for cs in career_skills_db]
    skill_lookup = {
        str(s.id): s for s in db.query(Skill).filter(Skill.id.in_(skill_ids)).all()
    }

    career_skills = []
    for cs in career_skills_db:
        skill = skill_lookup.get(str(cs.skill_id))
        if skill:
            career_skills.append({
                "skill_id": str(cs.skill_id),
                "importance_weight": cs.importance_weight,
                "category": skill.category
            })

    user_skills_db = db.query(UserSkill).filter(
        UserSkill.user_id == current_user.id,
        UserSkill.skill_id.in_(skill_ids)
    ).all()

    user_skills = []
    for us in user_skills_db:
        user_skills.append({
            "skill_id": str(us.skill_id),
            "proficiency": us.proficiency,
            "last_practiced": us.last_practiced if us.last_practiced else date.today()
        })

    result = compute_readiness_score(career_skills, user_skills)

    return {
        "success": True,
        "message": "Skill refreshed and score recalculated",
        "data": {
            "skill_id": skill_id,
            "last_practiced": str(date.today()),
            "updated_readiness": {
                "overall_score": result["overall_score"],
                "category_breakdown": result["category_breakdown"],
                "needs_review_count": result["needs_review_count"]
            }
        }
    }