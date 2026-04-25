from pydantic import BaseModel, Field
from typing import List
from uuid import UUID

class Runsheet(BaseModel):
    spots: List[UUID] = Field(default_factory=list)
