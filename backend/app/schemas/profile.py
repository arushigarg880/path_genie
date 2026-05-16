from pydantic import BaseModel, Field
from typing import Optional, Literal


class ProfileResponse(BaseModel):
    name: str
    academic_year: Optional[str] = None
    education: Optional[str] = None
    hours_per_day: Optional[float] = None
    learning_pace: Optional[Literal["slow", "normal", "fast"]] = None


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    academic_year: Optional[str] = Field(None, max_length=50)
    education: Optional[str] = Field(None, max_length=100)
    hours_per_day: Optional[float] = Field(None, gt=0, le=24)
    learning_pace: Optional[Literal["slow", "normal", "fast"]] = None