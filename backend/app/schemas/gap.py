# schemas/gap.py

from pydantic import BaseModel
from typing import List

class SkillGapItem(BaseModel):
    skill_id: str
    skill_name: str
    importance_weight: float
    is_core: bool
    estimated_hours: int
    category: str

class SkillGapResponse(BaseModel):
    critical: List[SkillGapItem]
    important: List[SkillGapItem]
    supplementary: List[SkillGapItem]
    total_missing: int
    total_required: int
    career_name: str
    career_id: str