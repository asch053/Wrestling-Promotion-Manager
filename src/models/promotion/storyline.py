from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class PlannedOutcome(str, Enum):
    TURN_FACE = "TURN_FACE"
    TURN_HEEL = "TURN_HEEL"
    PUSH_STAR = "PUSH_STAR"
    BUILD_RIVALRY = "BUILD_RIVALRY"

class Storyline(BaseModel):
    id: UUID
    name: str
    participants: List[UUID] = Field(default_factory=list)
    excitement: int = 50
    is_active: bool = True
    planned_outcome: PlannedOutcome
    target_wrestler: Optional[UUID] = None
