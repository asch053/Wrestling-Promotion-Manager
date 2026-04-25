from typing import Dict, List, Optional
from uuid import UUID
from src.models.wrestler.wrestler import Wrestler
from src.models.promotion.company import Company
from src.models.promotion.storyline import Storyline, PlannedOutcome

def calculate_morale_shift(wrestler: Wrestler, was_booked: bool, won: bool, company: Company, storylines: List[Storyline] = None, wrestler_id: UUID = None, championships: list = None) -> int:
    total_shift = 0
    
    # 1. Booking Result
    if not was_booked:
        base_shift = -5
    elif won:
        base_shift = 5
    else:
        base_shift = -3
    
    # 2. Ego Amplifier (only on negative shifts)
    if base_shift < 0:
        ego_multiplier = 1.0 + (wrestler.backstage.ego / 100.0)
        base_shift = int(round(base_shift * ego_multiplier))
    
    total_shift += base_shift
    
    # 3. Storyline Boost
    if storylines:
        for s in storylines:
            if s.is_active and s.planned_outcome == PlannedOutcome.PUSH_STAR and s.target_wrestler:
                # We need to check by matching wrestler identity. Since we don't have the UUID here,
                # we pass it in from the caller. For now, check if wrestler is referenced.
                # The caller should only pass storylines where this wrestler is the target.
                total_shift += 10
                break
    
    # 4. Financial Fairness
    if wrestler.contract and wrestler.contract.weekly_salary > 0:
        for peer in company.current_roster:
            if peer is wrestler:
                continue
            if peer.contract and peer.popularity.hype < wrestler.popularity.hype:
                if peer.contract.weekly_salary > wrestler.contract.weekly_salary:
                    total_shift -= 10
                    break  # Only triggers once
    
    # 5. The Hunger (Championship morale check)
    # Requires wrestler_id and championships to be passed
    if championships and wrestler_id:
        from src.engine.championship_manager import wrestler_holds_title, wrestler_holds_world_title
        if wrestler.backstage.ego > 70 and not wrestler_holds_title(wrestler_id, championships):
            total_shift -= 5
            if wrestler.popularity.hype > 80 and not wrestler_holds_world_title(wrestler_id, championships):
                total_shift -= 5
    
    return total_shift

def apply_morale_shift(wrestler: Wrestler, shift: int):
    wrestler.morale = max(0, min(100, wrestler.morale + shift))

def calculate_resign_difficulty(wrestler: Wrestler) -> float:
    return 1.0 - (wrestler.morale / 100.0)
