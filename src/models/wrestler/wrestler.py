from pydantic import BaseModel, Field, field_validator
from typing import Optional

class WrestlerBase(BaseModel):
    """
    The fundamental blueprint for every worker in your promotion.
    """
    name: str = Field(..., min_length=2, max_length=50)
    age: int = Field(..., ge=18, le=65)
    weight: float = Field(..., ge=50.0, le=150.0)  # in kg
    height: float = Field(..., ge=150.0, le=210.0)  # in cms
    
    # Physical Stats
    strength: int = Field(default=50, ge=0, le=100)
    agility: int = Field(default=50, ge=0, le=100)
    stamina: int = Field(default=50, ge=0, le=100)
    
    # Performance Stats
    charisma: int = Field(default=50, ge=0, le=100)
    mic_skill: int = Field(default=50, ge=0, le=100)
    heat: int = Field(default=50, ge=0, le=100)
    pop: int = Field(default=50, ge=0, le=100)
    
    # Career Stats
    overness: int = Field(default=10, ge=0, le=100) # Popularity
    momentum: int = Field(default=50, ge=0, le=100) # Current 'Heat'
    is_injured: bool = False
    
    @property
    def star_power(self) -> float:
        """Calculates the worker's drawing potential."""
        return (self.charisma * 0.6) + (self.overness * 0.4)

# TODO: add additional functions for 'WrestlerSkills', 'WrestlerHistory', FanIntreration, WrestlerPopularity, etc.