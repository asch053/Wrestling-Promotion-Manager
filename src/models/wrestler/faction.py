from pydantic import BaseModel, Field
from typing import List, Dict
from uuid import UUID
from .wrestler import Wrestler, Alignment

class Faction(BaseModel):
    id: UUID
    name: str
    leader_id: UUID
    members: List[UUID] = Field(default_factory=list)

    def get_dominant_alignment(self, roster_dict: Dict[UUID, Wrestler]) -> Alignment:
        if not self.members:
            return Alignment.TWEENER
        face_count = 0
        heel_count = 0
        for m_id in self.members:
            if m_id in roster_dict:
                a = roster_dict[m_id].alignment
                if a == Alignment.FACE:
                    face_count += 1
                elif a == Alignment.HEEL:
                    heel_count += 1
        if face_count > heel_count:
            return Alignment.FACE
        elif heel_count > face_count:
            return Alignment.HEEL
        else:
            return Alignment.TWEENER
