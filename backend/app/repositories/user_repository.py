from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date

from app.models.user import User
from app.models.skill import Skill, UserSkill


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def update_user_profile(db: Session, user: User, data: dict) -> User:
    for key, value in data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def get_user_skills(db: Session, user_id: UUID) -> list[UserSkill]:
    return db.query(UserSkill).filter(UserSkill.user_id == user_id).all()


def get_user_skill(db: Session, user_id: UUID, skill_id: UUID) -> UserSkill | None:
    return db.query(UserSkill).filter(
        UserSkill.user_id == user_id,
        UserSkill.skill_id == skill_id
    ).first()


def add_user_skill(db: Session, user_id: UUID, skill_id: UUID, proficiency: float) -> UserSkill:
    today = date.today()
    user_skill = UserSkill(
        user_id=user_id,
        skill_id=skill_id,
        proficiency=proficiency,
        date_added=today,
        last_practiced=today
    )
    db.add(user_skill)
    db.commit()
    db.refresh(user_skill)
    return user_skill


def delete_user_skill(db: Session, user_skill: UserSkill) -> None:
    db.delete(user_skill)
    db.commit()


def get_skill_by_id(db: Session, skill_id: UUID) -> Skill | None:
    return db.query(Skill).filter(Skill.id == skill_id).first()