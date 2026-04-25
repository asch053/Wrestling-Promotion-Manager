from enum import Enum
from pydantic import BaseModel, model_validator
from typing import List, Optional
from uuid import UUID
from .runsheet import Runsheet
from src.engine.stipulation_logic_handler import MatchStipulation

class MatchType(str, Enum):
    ONE_ON_ONE = "ONE_ON_ONE"
    TWO_ON_TWO = "TWO_ON_TWO"
    THREE_ON_THREE = "THREE_ON_THREE"

class ScriptingStyle(str, Enum):
    STRICT = "STRICT"
    AUDIBLE = "AUDIBLE"
    CALLED_IN_RING = "CALLED_IN_RING"

class BookingSheet(BaseModel):
    match_type: MatchType
    teams: List[List[UUID]]
    scripting_style: ScriptingStyle
    designated_winner: UUID
    expected_runsheet: Optional[Runsheet] = None
    storyline_id: Optional[UUID] = None
    championship_id: Optional[UUID] = None
    stipulation: MatchStipulation = MatchStipulation.STANDARD

    @model_validator(mode='after')
    def check_runsheet_provided(self):
        if self.scripting_style in [ScriptingStyle.STRICT, ScriptingStyle.AUDIBLE]:
            if not self.expected_runsheet:
                raise ValueError(f"expected_runsheet must be provided for {self.scripting_style.value} matches")
        return self

    @model_validator(mode='after')
    def check_winner_in_teams(self):
        flat_participants = [w_id for team in self.teams for w_id in team]
        if self.designated_winner not in flat_participants:
            raise ValueError("designated_winner must be one of the participants")
        return self
