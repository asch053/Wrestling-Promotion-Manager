from pydantic import BaseModel, Field

class GameState(BaseModel):
    current_day: int = Field(ge=1, le=7, default=1)
    week_number: int = Field(ge=1, default=1)
    year: int = Field(ge=1900, default=2026)
