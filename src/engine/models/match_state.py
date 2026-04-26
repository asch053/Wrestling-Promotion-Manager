from pydantic import BaseModel
from typing import Dict
from uuid import UUID

class WrestlerState(BaseModel):
    integrity: int
    stamina: int
    momentum: int = 50

class MatchState(BaseModel):
    wrestlers: Dict[UUID, WrestlerState]
    crowd_excitement: int = 50
