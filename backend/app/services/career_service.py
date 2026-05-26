from sqlalchemy.orm import Session
from uuid import UUID
from app.models.career import Career, CareerSkill, UserCareer
from app.models.user import User

from app.models.skill import Skill  

def get_all_careers(db: Session):
    return db.query(Career).all()
def get_career_by_id(db: Session, career_id: UUID):
    career = db.query(Career).filter(Career.id == career_id).first()
    if not career:
        raise ValueError("Career not found")
    return career
def select_career(db: Session, user: User, career_id: UUID):
    career = get_career_by_id(db, career_id)
    
    # Purane active career ko deactivate karo
    db.query(UserCareer).filter(
        UserCareer.user_id == user.id,
        UserCareer.is_active == True
    ).update({"is_active": False})
    
    # Naya career select karo
    new_selection = UserCareer(
        user_id=user.id,
        career_id=career_id,
        is_active=True
    )
    db.add(new_selection)
    db.commit()
    
    return career

def get_career_skills_list(db, career_skills):
    result = []
    for cs in career_skills:
        skill = db.query(Skill).filter(Skill.id == cs.skill_id).first()
        if skill:
            result.append({
                "name": skill.name,
                "importance_weight": cs.importance_weight,
                "is_core": cs.is_core
            })
    return result
def compare_careers(db: Session, user: User, career_id_a: UUID, career_id_b: UUID):
    career_a = get_career_by_id(db, career_id_a)
    career_b = get_career_by_id(db, career_id_b)

    from app.models.skill import UserSkill
    user_skill_ids = [
        us.skill_id for us in
        db.query(UserSkill).filter(UserSkill.user_id == user.id).all()
    ]

    skills_a = db.query(CareerSkill).filter(
        CareerSkill.career_id == career_id_a
    ).all()

    skills_b = db.query(CareerSkill).filter(
        CareerSkill.career_id == career_id_b
    ).all()

    def get_overlap(career_skills):
        total = len(career_skills)
        matched = sum(1 for cs in career_skills if cs.skill_id in user_skill_ids)
        return round((matched / total * 100), 1) if total > 0 else 0.0

    return {
        "career_a": {
            "id": str(career_a.id),
            "name": career_a.name,
            "math_intensity": career_a.math_intensity,
            "coding_intensity": career_a.coding_intensity,
            "estimated_prep_weeks": career_a.estimated_prep_weeks,
            "required_skills": get_career_skills_list(db, skills_a),
            "your_overlap_percent": get_overlap(skills_a)
        },
        "career_b": {
            "id": str(career_b.id),
            "name": career_b.name,
            "math_intensity": career_b.math_intensity,
            "coding_intensity": career_b.coding_intensity,
            "estimated_prep_weeks": career_b.estimated_prep_weeks,
            "required_skills": get_career_skills_list(db, skills_b),
            "your_overlap_percent": get_overlap(skills_b)
        },
        "better_fit": career_a.name if get_overlap(skills_a) >= get_overlap(skills_b) else career_b.name
    }