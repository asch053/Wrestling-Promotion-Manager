from typing import Dict
from uuid import UUID
from src.models.wrestler.faction import Faction
from src.models.wrestler.wrestler import Wrestler, Alignment

def get_bloat_penalty(faction: Faction) -> int:
    return max(0, len(faction.members) - 4) * 10

def can_join_faction(wrestler: Wrestler, faction: Faction, leader: Wrestler, wrestler_id: UUID, roster_dict: Dict[UUID, Wrestler] = None) -> bool:
    # Use dynamic alignment check
    faction_alignment = Alignment.TWEENER
    if roster_dict:
        faction_alignment = faction.get_dominant_alignment(roster_dict)

    wrestler_alignment = wrestler.alignment

    # Tweeners can join either side
    if wrestler_alignment != Alignment.TWEENER:
        if faction_alignment != Alignment.TWEENER and wrestler_alignment != faction_alignment:
            return False

    leader_id = faction.leader_id
    if leader_id in wrestler.friendships and wrestler.friendships[leader_id] > 60:
        return True

    if wrestler.popularity.hype > 80 and wrestler.backstage.ego < 50:
        return True

    return False

def get_faction_hype(faction: Faction, roster_dict: Dict[UUID, Wrestler]) -> float:
    if not faction.members:
        return 0.0
    total = sum(roster_dict[m].popularity.hype for m in faction.members if m in roster_dict)
    return total / len(faction.members)
