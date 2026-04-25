from enum import Enum
from pydantic import BaseModel, Field

class MoveType(str, Enum):
    STRIKE = "STRIKE"
    GRAPPLE = "GRAPPLE"
    SUBMISSION = "SUBMISSION"
    AERIAL = "AERIAL"
    FINISHER = "FINISHER"

class Move(BaseModel):
    name: str
    damage: int = Field(ge=0, le=100)
    stamina_cost: int = Field(ge=0, le=100)
    heat_generation: int = Field(ge=0, le=100)
    move_type: MoveType
