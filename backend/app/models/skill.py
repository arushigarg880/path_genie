import uuid
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import date
from app.db.base import Base



from app.core.enums import LearningPace


class Skill(Base):
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    estimated_hours = Column(Integer, nullable=False)
    category = Column(String(50), nullable=True)  # e.g. "language", "framework"


class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    proficiency = Column(Float, nullable=False, default=0.5)   # 0.0 - 1.0
    last_practiced = Column(Date, nullable=True, default=date.today)
    date_added = Column(Date, server_default=func.current_date())
    __table_args__ = (
        UniqueConstraint('user_id', 'skill_id', name='uq_user_skill'),
    )
class SkillPrerequisite(Base):
    __tablename__ = "skill_prerequisites"

    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), primary_key=True)
    requires_skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), primary_key=True)