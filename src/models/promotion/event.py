from enum import Enum
from pydantic import BaseModel, Field
from typing import List
from src.engine.models.match_report import MatchReport

class EventScale(str, Enum):
    HOUSE_SHOW = "HOUSE_SHOW"
    TV_TAPING = "TV_TAPING"
    PPV = "PPV"
    MEGA_EVENT = "MEGA_EVENT"

class Event(BaseModel):
    name: str
    location: str
    scale: EventScale
    match_reports: List[MatchReport] = Field(default_factory=list)
