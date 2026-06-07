# app/models/resource.py

from sqlalchemy import Column, String, Integer, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class SkillResource(Base):
    __tablename__ = "skill_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    resource_type = Column(String(50), nullable=False)
    priority = Column(Integer, default=1)


class CareerProject(Base):
    __tablename__ = "career_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    career_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    difficulty = Column(String(20), nullable=False)
    skills_practiced = Column(ARRAY(UUID(as_uuid=True)), default=[])