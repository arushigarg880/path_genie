import uuid
from sqlalchemy import Column, String, Text, Integer, Float, Boolean,ForeignKey, UniqueConstraint,DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

class Career(Base):
    __tablename__ = "careers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    math_intensity = Column(Integer, nullable=False)      # 1-5
    coding_intensity = Column(Integer, nullable=False)    # 1-5
    estimated_prep_weeks = Column(Integer, nullable=False)


class CareerSkill(Base):
    __tablename__ = "career_skills"

    career_id = Column(UUID(as_uuid=True), ForeignKey("careers.id"), primary_key=True)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), primary_key=True)
    importance_weight = Column(Float, nullable=False)     # 0.0 - 1.0
    is_core = Column(Boolean, default=False)

class UserCareer(Base):
    __tablename__ = "user_careers"

    id=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    career_id = Column(UUID(as_uuid=True), ForeignKey("careers.id"), nullable=False)
    selected_at=Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

class UserRoadmap(Base):
    __tablename__ = "user_roadmaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    career_id = Column(UUID(as_uuid=True), ForeignKey("careers.id"), nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    roadmap_data = Column(JSONB, nullable=True)
    version = Column(Integer, default=1)
    stability_score = Column(Float, default=1.0)


class RoadmapPhase(Base):
    __tablename__ = "roadmap_phases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roadmap_id = Column(UUID(as_uuid=True), ForeignKey("user_roadmaps.id"), nullable=False)
    phase_number = Column(Integer, nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    status = Column(String(20), default="pending")   # pending, in_progress, completed
    completed_at = Column(DateTime(timezone=True), nullable=True) 