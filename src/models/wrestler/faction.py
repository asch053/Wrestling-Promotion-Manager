from pydantic import BaseModel, Field
from typing import List, Dict
from uuid import UUID
from .wrestler import Wrestler, KayfabeStatus

class Faction(BaseModel):
    id: UUID
    name: str
    leader_id: UUID
    members: List[UUID] = Field(default_factory=list)

    def get_dominant_kayfabe_status(self, roster_dict: Dict[UUID, Wrestler]) -> KayfabeStatus:
        if not self.members:
            return KayfabeStatus.TWEENER
        face_count = 0
        heel_count = 0
        for m_id in self.members:
            if m_id in roster_dict:
                a = roster_dict[m_id].kayfabe_status
                if a == KayfabeStatus.FACE:
                    face_count += 1
                elif a == KayfabeStatus.HEEL:
                    heel_count += 1
        if face_count > heel_count:
            return KayfabeStatus.FACE
        elif heel_count > face_count:
            return KayfabeStatus.HEEL
        else:
            return KayfabeStatus.TWEENER
