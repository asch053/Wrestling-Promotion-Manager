from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class ChampionshipType(str, Enum):
    SINGLES = "SINGLES"
    TAG_TEAM = "TAG_TEAM"

class ChampionshipTier(str, Enum):
    WORLD = "WORLD"
    MID_CARD = "MID_CARD"

class TitleReign(BaseModel):
    holder_id: UUID
    holder_name: str
    defenses: int = 0
    start_event: str
    end_event: Optional[str] = None

class Championship(BaseModel):
    id: UUID
    name: str
    prestige: int = Field(ge=0, le=100, default=50)
    championship_type: ChampionshipType
    tier: ChampionshipTier
    is_active: bool = True
    current_holder: Optional[UUID] = None
    title_history: List[TitleReign] = Field(default_factory=list)
