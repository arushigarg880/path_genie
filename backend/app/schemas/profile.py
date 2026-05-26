from pydantic import BaseModel, Field,ConfigDict
from typing import Optional
from uuid import UUID
from datetime import date
from enum import Enum
from app.core.enums import LearningPace


# --- Profile Schemas ---

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    education: Optional[str] = None
    academic_year: Optional[str] = None
    hours_per_day: Optional[float] = Field(None, ge=0.5, le=24.0)
    learning_pace: Optional[LearningPace] = None



class ProfileResponse(BaseModel):
    id: UUID
    name: str
    email: str
    education: Optional[str]
    academic_year: Optional[str]
    hours_per_day: Optional[float]
    learning_pace: Optional[str]
    is_profile_complete: bool
    regeneration_needed: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)



class SkillAddRequest(BaseModel):
    skill_id: UUID
    proficiency: float = Field(..., ge=0.0, le=1.0)


class UserSkillResponse(BaseModel):
    skill_id: UUID
    skill_name: str
    proficiency: float
    date_added: date
    last_practiced: date

    model_config = ConfigDict(from_attributes=True)