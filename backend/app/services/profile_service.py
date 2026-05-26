from sqlalchemy.orm import Session
from uuid import UUID

from app.models.user import User
from app.schemas.profile import ProfileUpdate, ProfileResponse, UserSkillResponse
from app.repositories.user_repository import (
    get_user_by_id,
    update_user_profile,
    get_user_skills,
    get_user_skill,
    add_user_skill,
    delete_user_skill,
    get_skill_by_id
)


def is_profile_complete(user: User) -> bool:
    return all([
        user.education,
        user.academic_year,
        user.hours_per_day,
        user.learning_pace
    ])


def get_profile(db: Session, user: User) -> ProfileResponse:
    return ProfileResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        education=user.education,
        academic_year=user.academic_year,
        hours_per_day=user.hours_per_day,
        learning_pace=user.learning_pace,
        is_profile_complete=is_profile_complete(user)
    )


def update_profile(db: Session, user: User, data: ProfileUpdate) -> ProfileResponse:
    update_data = data.model_dump(exclude_none=True)

    regeneration_needed = any(
        key in update_data for key in ["hours_per_day", "learning_pace"]
    )

    updated_user = update_user_profile(db, user, update_data)

    response = get_profile(db, updated_user)
    response.regeneration_needed = regeneration_needed
    return response


def add_skill(db: Session, user: User, skill_id: UUID, proficiency: float) -> UserSkillResponse:
    skill = get_skill_by_id(db, skill_id)
    if not skill:
        raise ValueError("Skill not found")

    existing = get_user_skill(db, user.id, skill_id)
    if existing:
        raise ValueError("Skill already added")

    user_skill = add_user_skill(db, user.id, skill_id, proficiency)

    return UserSkillResponse(
        skill_id=user_skill.skill_id,
        skill_name=skill.name,
        proficiency=user_skill.proficiency,
        date_added=user_skill.date_added,
        last_practiced=user_skill.last_practiced
    )


def remove_skill(db: Session, user: User, skill_id: UUID) -> None:
    user_skill = get_user_skill(db, user.id, skill_id)
    if not user_skill:
        raise ValueError("Skill not found in your profile")

    delete_user_skill(db, user_skill)


def get_skills(db: Session, user: User) -> list[UserSkillResponse]:
    user_skills = get_user_skills(db, user.id)

    result = []
    for us in user_skills:
        skill = get_skill_by_id(db, us.skill_id)
        result.append(UserSkillResponse(
            skill_id=us.skill_id,
            skill_name=skill.name,
            proficiency=us.proficiency,
            date_added=us.date_added,
            last_practiced=us.last_practiced
        ))
    return result