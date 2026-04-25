from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from uuid import UUID

class StatDelta(BaseModel):
    hype_delta: int = 0
    pop_delta: int = 0
    heat_delta: int = 0

class MatchReport(BaseModel):
    play_by_play: List[str] = Field(default_factory=list)
    star_rating: float
    final_crowd_excitement: int
    wrestler_deltas: Dict[UUID, StatDelta] = Field(default_factory=dict)
    storyline_delta: int = 0
    storyline_id: Optional[UUID] = None
    championship_id: Optional[UUID] = None
    prestige_delta: int = 0
