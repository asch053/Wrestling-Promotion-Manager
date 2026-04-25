from pydantic import BaseModel, Field
from typing import List, Dict
from .event import Event
from src.models.wrestler.wrestler import Wrestler
from src.models.promotion.storyline import Storyline
from src.models.promotion.championship import Championship, ChampionshipTier
from src.models.promotion.dojo import Dojo

class Company(BaseModel):
    name: str
    bank_balance: int = 1000000
    current_roster: List[Wrestler] = Field(default_factory=list)
    past_roster: List[Wrestler] = Field(default_factory=list)
    past_events: List[Event] = Field(default_factory=list)
    storylines: List[Storyline] = Field(default_factory=list)
    championships: List[Championship] = Field(default_factory=list)
    dojos: List[Dojo] = Field(default_factory=list)
    base_excitement_modifier: float = 0.0
    medical_staff_level: int = Field(ge=1, le=5, default=1)
    stipulation_usage: Dict[str, int] = Field(default_factory=dict)

    def calculate_current_hype(self) -> float:
        total_hype = sum(w.popularity.hype for w in self.current_roster)
        decay = 1.0
        for w in reversed(self.past_roster):
            decay *= 0.8
            total_hype += w.popularity.hype * decay
        # WORLD title hierarchy bonus
        for c in self.championships:
            if c.is_active and c.tier == ChampionshipTier.WORLD:
                total_hype += c.prestige * 2
        return total_hype

    def calculate_current_excitement(self) -> float:
        total_excitement = self.base_excitement_modifier
        decay = 1.0
        for e in reversed(self.past_events):
            # Calculate average excitement for the event
            if e.match_reports:
                event_excitement = sum(mr.final_crowd_excitement for mr in e.match_reports) / len(e.match_reports)
            else:
                event_excitement = 50.0
            
            total_excitement += event_excitement * decay
            decay *= 0.8
        
        # MID_CARD title hierarchy bonus
        for c in self.championships:
            if c.is_active and c.tier == ChampionshipTier.MID_CARD:
                total_excitement += c.prestige
        
        # If no events, return a base excitement
        if total_excitement == 0.0:
            return 50.0
        return total_excitement
