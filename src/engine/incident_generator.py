import random
from enum import Enum
from pydantic import BaseModel
from typing import Dict, List, Optional
from uuid import UUID
from src.models.wrestler.wrestler import Wrestler
from src.models.promotion.company import Company

class IncidentType(str, Enum):
    REFUSAL_TO_LOSE = "REFUSAL_TO_LOSE"
    LOCKER_ROOM_POISON = "LOCKER_ROOM_POISON"
    PUBLIC_SHOOTING = "PUBLIC_SHOOTING"

class Incident(BaseModel):
    wrestler_id: UUID
    incident_type: IncidentType
    description: str

def generate_incidents(company: Company, roster_dict: Dict[UUID, Wrestler]) -> List[Incident]:
    if company.game_state.current_day != 6:
        raise PermissionError("Incidents can only be generated on Day 6.")
    incidents = []
    
    for w_id, w in roster_dict.items():
        if w.backstage.ego > 70 and w.backstage.professionalism < 40 and w.morale < 30:
            r = random.random()
            if r < 0.3:
                incidents.append(Incident(
                    wrestler_id=w_id,
                    incident_type=IncidentType.REFUSAL_TO_LOSE,
                    description=f"{w.name} is refusing to do the job! They won't lay down for anyone."
                ))
            elif r < 0.7:
                incidents.append(Incident(
                    wrestler_id=w_id,
                    incident_type=IncidentType.LOCKER_ROOM_POISON,
                    description=f"{w.name} is poisoning the locker room, spreading negativity backstage."
                ))
            else:
                incidents.append(Incident(
                    wrestler_id=w_id,
                    incident_type=IncidentType.PUBLIC_SHOOTING,
                    description=f"{w.name} has gone public, criticizing the company in an interview!"
                ))
    
    return incidents

def apply_incident(incident: Incident, company: Company, roster_dict: Dict[UUID, Wrestler]):
    if incident.incident_type == IncidentType.LOCKER_ROOM_POISON:
        troublemaker = roster_dict.get(incident.wrestler_id)
        if troublemaker and troublemaker.faction_id:
            # Poison faction members
            for w_id, w in roster_dict.items():
                if w.faction_id == troublemaker.faction_id and w_id != incident.wrestler_id:
                    w.morale = max(0, w.morale - 15)
        else:
            # No faction: poison 2 random roster members
            others = [w_id for w_id in roster_dict if w_id != incident.wrestler_id]
            targets = random.sample(others, min(2, len(others)))
            for t_id in targets:
                roster_dict[t_id].morale = max(0, roster_dict[t_id].morale - 5)
                
    elif incident.incident_type == IncidentType.PUBLIC_SHOOTING:
        company.base_excitement_modifier -= 5
