from typing import Dict, Optional
from uuid import UUID
from src.models.promotion.championship import Championship, ChampionshipTier, TitleReign
from src.models.promotion.company import Company
from src.models.wrestler.wrestler import Wrestler

def award_title(championship: Championship, wrestler_id: UUID, wrestler_name: str, event_name: str):
    # Close any existing reign
    if championship.current_holder and championship.title_history:
        championship.title_history[-1].end_event = event_name
    
    championship.current_holder = wrestler_id
    championship.title_history.append(TitleReign(
        holder_id=wrestler_id,
        holder_name=wrestler_name,
        start_event=event_name
    ))

def vacate_title(championship: Championship, event_name: str):
    if championship.current_holder and championship.title_history:
        championship.title_history[-1].end_event = event_name
    championship.current_holder = None

def retire_title(championship: Championship, event_name: str = "Retired"):
    if championship.current_holder:
        vacate_title(championship, event_name)
    championship.is_active = False

def unretire_title(championship: Championship):
    championship.is_active = True

def update_prestige(championship: Championship, star_rating: float):
    delta = int(round((star_rating - 3.0) * 5))
    championship.prestige = max(0, min(100, championship.prestige + delta))
    # Increment defenses on current reign
    if championship.current_holder and championship.title_history:
        championship.title_history[-1].defenses += 1

def calculate_saturation_penalty(company: Company) -> int:
    active_count = len([c for c in company.championships if c.is_active])
    if active_count <= 4:
        return 0
    excitement = company.calculate_current_excitement()
    return int(max(0, (active_count - 4) * 0.05 * excitement))

def check_hierarchy_violation(wrestler: Wrestler, championship: Championship) -> bool:
    if championship.tier == ChampionshipTier.WORLD and wrestler.popularity.hype < 60:
        return True
    return False

def get_champion_prestige(wrestler_id: UUID, championships: list) -> int:
    """Return the highest prestige of any active championship held by this wrestler."""
    max_prestige = 0
    for c in championships:
        if c.is_active and c.current_holder == wrestler_id:
            max_prestige = max(max_prestige, c.prestige)
    return max_prestige

def wrestler_holds_title(wrestler_id: UUID, championships: list) -> bool:
    return any(c.is_active and c.current_holder == wrestler_id for c in championships)

def wrestler_holds_world_title(wrestler_id: UUID, championships: list) -> bool:
    return any(c.is_active and c.current_holder == wrestler_id and c.tier == ChampionshipTier.WORLD for c in championships)
