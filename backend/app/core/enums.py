# app/core/enums.py
from enum import Enum

class LearningPace(str, Enum):
    slow = "slow"
    normal = "normal"
    fast = "fast"