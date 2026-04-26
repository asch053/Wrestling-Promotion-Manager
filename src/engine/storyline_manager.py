from typing import Dict, List
from uuid import UUID
from src.models.promotion.company import Company
from src.models.promotion.storyline import Storyline, PlannedOutcome
from src.models.promotion.event import Event
from src.models.wrestler.wrestler import Wrestler, KayfabeStatus

def decay_inactive_storylines(company: Company, event: Event):
    # Find active storylines featured in the event
    featured_storylines = set()
    for report in event.match_reports:
        if report.storyline_id:
            featured_storylines.add(report.storyline_id)
            
    # Decay ones not featured
    for storyline in company.storylines:
        if storyline.is_active and storyline.id not in featured_storylines:
            storyline.excitement = max(0, storyline.excitement - 10)

def execute_payoff(company: Company, roster_dict: Dict[UUID, Wrestler], storyline: Storyline):
    if company.game_state.current_day != 4:
        raise PermissionError("Storylines can only be payoff'd during the Thursday Creative Meeting (Day 4).")
        
    if not storyline.is_active:
        return
        
    # Cash in excitement to the company
    momentum_boost = int(storyline.excitement / 10)
    company.base_excitement_modifier += momentum_boost
    
    target_id = storyline.target_wrestler
    if target_id and target_id in roster_dict:
        target = roster_dict[target_id]
        
        if storyline.planned_outcome == PlannedOutcome.TURN_HEEL:
            # Inject massive Heat spike, drain Pop -> dynamic alignment shifts to HEEL
            target.popularity.heat = min(100, target.popularity.heat + 40)
            target.popularity.pop = max(0, target.popularity.pop - 30)
            # Destroy friendships with current Faces, create rivalries
            to_remove = []
            for friend_id, score in target.friendships.items():
                if friend_id in roster_dict and roster_dict[friend_id].kayfabe_status == KayfabeStatus.FACE:
                    to_remove.append(friend_id)
            for f_id in to_remove:
                del target.friendships[f_id]
                target.rivalries[f_id] = 100
                roster_dict[f_id].rivalries[target_id] = 100
                if target_id in roster_dict[f_id].friendships:
                    del roster_dict[f_id].friendships[target_id]
                    
        elif storyline.planned_outcome == PlannedOutcome.TURN_FACE:
            # Inject massive Pop spike, drain Heat -> dynamic alignment shifts to FACE
            target.popularity.pop = min(100, target.popularity.pop + 40)
            target.popularity.heat = max(0, target.popularity.heat - 30)
            # Destroy friendships with current Heels, create rivalries
            to_remove = []
            for friend_id, score in target.friendships.items():
                if friend_id in roster_dict and roster_dict[friend_id].kayfabe_status == KayfabeStatus.HEEL:
                    to_remove.append(friend_id)
            for f_id in to_remove:
                del target.friendships[f_id]
                target.rivalries[f_id] = 100
                roster_dict[f_id].rivalries[target_id] = 100
                if target_id in roster_dict[f_id].friendships:
                    del roster_dict[f_id].friendships[target_id]
                    
        elif storyline.planned_outcome == PlannedOutcome.PUSH_STAR:
            boost = int(storyline.excitement / 2)
            target.popularity.hype = min(100, target.popularity.hype + boost)
            
        elif storyline.planned_outcome == PlannedOutcome.BUILD_RIVALRY:
            # Add rivalry to all other participants
            for p_id in storyline.participants:
                if p_id != target_id and p_id in roster_dict:
                    target.rivalries[p_id] = 100
                    roster_dict[p_id].rivalries[target_id] = 100
                    
    storyline.is_active = False
