# services/gap_service.py

from sqlalchemy.orm import Session
from app.models.career import CareerSkill, UserCareer
from app.models.skill import Skill, UserSkill
from app.engines.skill_gap_engine import analyze_skill_gap
import uuid

def get_skill_gap_for_user(user_id: uuid.UUID, db: Session) -> dict:
    """
    1. Find user's active career
    2. Get all skills that career requires (from career_skills table)
    3. Get all skills the user already knows (from user_skills table)
    4. Pass both to the engine and return the result
    """

    # Step 1: Find active career
    # WHY filter is_active=True? A user can switch careers.
    # We only care about their CURRENT target.
    user_career = db.query(UserCareer).filter(
        UserCareer.user_id == user_id,
        UserCareer.is_active == True
    ).first()

    if not user_career:
        return {"error": "No active career selected. Please select a career first."}

    # Step 2: Get all skills required by this career
    # We join CareerSkill with Skill to also get the skill name
    career_skill_rows = (
        db.query(CareerSkill, Skill)
        .join(Skill, Skill.id == CareerSkill.skill_id)
        .filter(CareerSkill.career_id == user_career.career_id)
        .all()
    )

    # Format into a clean list of dicts for the engine
    career_skills = [
        {
            "skill_id": str(cs.skill_id),
            "skill_name": skill.name,
            "importance_weight": cs.importance_weight,
            "is_core": cs.is_core,
            "estimated_hours": skill.estimated_hours,
            "category": skill.category
        }
        for cs, skill in career_skill_rows
    ]

    # Step 3: Get skills user already knows
    user_skill_rows = db.query(UserSkill).filter(
        UserSkill.user_id == user_id
    ).all()

    user_skill_ids = [str(us.skill_id) for us in user_skill_rows]

    # Step 4: Pass to engine and return result
    gap_result = analyze_skill_gap(user_skill_ids, career_skills)

    # Add career name to response so frontend knows which career this is for
    from app.models.career import Career
    career = db.query(Career).filter(
        Career.id == user_career.career_id
    ).first()

    gap_result["career_name"] = career.name if career else "Unknown"
    gap_result["career_id"] = str(user_career.career_id)

    return gap_result