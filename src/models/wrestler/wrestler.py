from enum import Enum
from pydantic import BaseModel, Field
from typing import Set, Optional, Dict
from uuid import UUID
from .contract import Contract
from .injury import Injury

class KayfabeStatus(str, Enum):
    FACE = "FACE"
    HEEL = "HEEL"
    TWEENER = "TWEENER"

class WrestlerStyle(str, Enum):
    HEAVY_HITTER = "HEAVY_HITTER"
    GRAPPLER = "GRAPPLER"
    HIGH_FLYER = "HIGH_FLYER"
    BRAWLER = "BRAWLER"
    SHOWMAN = "SHOWMAN"
    DIRTY_TRICKS = "DIRTY_TRICKS"
    MEAN_STREAK = "MEAN_STREAK"
    # Future styles are additive — append here without touching any other logic

class InRingSkill(BaseModel):
    strength: int = Field(ge=0, le=100)
    agility: int = Field(ge=0, le=100)
    stamina: int = Field(ge=0, le=100)

class Psychology(BaseModel):
    work_rate: int = Field(ge=0, le=100)
    selling: int = Field(ge=0, le=100)
    intelligence: int = Field(ge=0, le=100, default=50)

class Backstage(BaseModel):
    ego: int = Field(ge=0, le=100)
    professionalism: int = Field(ge=0, le=100)

class Popularity(BaseModel):
    hype: int = Field(ge=0, le=100, default=50)
    heat: int = Field(ge=0, le=100, default=50)
    pop: int = Field(ge=0, le=100, default=50)

class Wrestler(BaseModel):
    name: str
    popularity: Popularity = Field(default_factory=Popularity)
    in_ring: InRingSkill
    psychology: Psychology
    backstage: Backstage
    contract: Optional[Contract] = None
    moveset: Set[UUID] = Field(default_factory=set)
    friendships: Dict[UUID, int] = Field(default_factory=dict)
    rivalries: Dict[UUID, int] = Field(default_factory=dict)
    faction_id: Optional[UUID] = None
    morale: int = Field(ge=0, le=100, default=50)
    wins: int = 0
    losses: int = 0
    fatigue: int = Field(ge=0, le=100, default=0)
    injury_status: Optional[Injury] = None
    style: Optional[WrestlerStyle] = None

    @property
    def resonance_ratio(self) -> int:
        return max(-100, min(100, self.popularity.pop - self.popularity.heat))

    @property
    def kayfabe_status(self) -> KayfabeStatus:
        res = self.resonance_ratio
        if res > 20:
            return KayfabeStatus.FACE
        elif res < -20:
            return KayfabeStatus.HEEL
        else:
            return KayfabeStatus.TWEENER