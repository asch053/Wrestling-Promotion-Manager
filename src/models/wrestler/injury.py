from enum import Enum
from pydantic import BaseModel
from typing import Optional

class InjuryType(str, Enum):
    MINOR = "MINOR"
    MAJOR = "MAJOR"

class Injury(BaseModel):
    name: str
    injury_type: InjuryType
    weeks_remaining: float
    affected_stat: Optional[str] = None # e.g., "agility", "strength"
    is_sidelined: bool = False
