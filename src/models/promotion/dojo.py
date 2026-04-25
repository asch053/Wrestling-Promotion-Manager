from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
from src.models.wrestler.wrestler import Wrestler


class DojoStyle(str, Enum):
    STRONG_STYLE = "STRONG_STYLE"
    TECHNICAL = "TECHNICAL"
    LUCHA = "LUCHA"
    BRAWLER = "BRAWLER"
    SHOWMAN = "SHOWMAN"
    # Future styles are additive — append here without touching any other logic


class DojoManager(BaseModel):
    name: str
    scouting_skill: int = Field(ge=0, le=100, default=50)
    training_skill: int = Field(ge=0, le=100, default=50)


class Dojo(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    style: DojoStyle
    prestige_stars: int = Field(ge=0, le=5, default=1)
    equipment_level: int = Field(ge=1, le=5, default=1)
    appeal: int = Field(ge=0, le=100, default=50)
    xp: int = 0
    manager: DojoManager
    students: List[Wrestler] = Field(default_factory=list)
    graduates: List[UUID] = Field(default_factory=list)  # IDs of wrestlers on main roster
