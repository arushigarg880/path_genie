from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from app.db.session import SessionLocal
from app.core.dependencies import get_current_user
from app.models.career import UserCareer, CareerSkill
from app.models.skill import Skill, UserSkill, SkillPrerequisite
from app.engines.readiness_engine import compute_readiness_score, decayed_proficiency
from app.engines.psd_engine import compute_overall_psd

router = APIRouter(prefix="/psd", tags=["PSD"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def get_psd_score(
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

    # Step 3: Build career_skills list
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

    # Step 4: Get user's known skills with decay
    user_skills_db = db.query(UserSkill).filter(
        UserSkill.user_id == current_user.id,
        UserSkill.skill_id.in_(skill_ids)
    ).all()

    today = date.today()
    user_skills = []
    for us in user_skills_db:
        user_skills.append({
            "skill_id": str(us.skill_id),
            "proficiency": us.proficiency,
            "last_practiced": us.last_practiced if us.last_practiced else today
        })

    # Step 5: Build user_proficiency_map (with decay)
    user_proficiency_map = {}
    for us in user_skills:
        days = (today - us["last_practiced"]).days
        user_proficiency_map[us["skill_id"]] = decayed_proficiency(
            us["proficiency"], days
        )

    # Step 6: Build prerequisite_map — fetch ALL skills' prereqs
    # (not just career skills) so recursive chain is complete
    all_prereqs_db = db.query(SkillPrerequisite).all()

    prerequisite_map = {}
    for p in all_prereqs_db:
        sid = str(p.skill_id)
        prereq_id = str(p.requires_skill_id)
        if sid not in prerequisite_map:
            prerequisite_map[sid] = []
        prerequisite_map[sid].append(prereq_id)

    # Step 7: Compute standard readiness score (M7)
    readiness_result = compute_readiness_score(career_skills, user_skills)

    # Step 8: Compute PSD score (M8)
    psd_result = compute_overall_psd(career_skills, user_proficiency_map, prerequisite_map)

    return {
        "success": True,
        "message": "PSD score computed",
        "data": {
            "standard_readiness_score": readiness_result["overall_score"],
            "psd_readiness_score": psd_result["overall_psd_score"],
            "explanation": psd_result["explanation"],
            "prerequisite_gap_count": psd_result["prerequisite_gap_count"],
            "needs_review_count": readiness_result["needs_review_count"],
            "skill_details": psd_result["skill_details"]
        }
    }