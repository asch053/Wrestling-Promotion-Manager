import random
from enum import Enum
from pydantic import BaseModel
from typing import Dict, List, Optional
from uuid import UUID


class MatchStipulation(str, Enum):
    STANDARD = "STANDARD"
    HARDCORE = "HARDCORE"
    STEEL_CAGE = "STEEL_CAGE"
    LADDER = "LADDER"
    SUBMISSION_ONLY = "SUBMISSION_ONLY"
    # Future stipulations are additive — append here, no other file changes needed


class StipulationModifiers(BaseModel):
    heat_multiplier: float = 1.0
    injury_chance_multiplier: float = 1.0
    stamina_cost_multiplier: float = 1.0
    damage_multiplier: float = 1.0
    star_rating_bonus: float = 0.0
    star_rating_penalty: float = 0.0
    production_cost: int = 0
    fatigue_multiplier: float = 1.0
    min_turn_bonus: int = 0
    difficulty_rating: int = 1
    required_skills: Dict[str, int] = {}
    danger_profile: List[str] = []


# --- Lookup Table ---
STIPULATION_MODIFIERS: Dict[MatchStipulation, StipulationModifiers] = {
    MatchStipulation.STANDARD: StipulationModifiers(),

    MatchStipulation.HARDCORE: StipulationModifiers(
        heat_multiplier=2.0,
        injury_chance_multiplier=2.5,
        stamina_cost_multiplier=1.5,
        damage_multiplier=1.5,
        star_rating_bonus=0.75,
        star_rating_penalty=0.75,
        production_cost=0,
        fatigue_multiplier=1.5,
        min_turn_bonus=0,
        difficulty_rating=2,
        required_skills={"strength": 55, "stamina": 50},
        danger_profile=["Unprotected chair shot", "Table spot", "Barbed wire contact"],
    ),

    MatchStipulation.STEEL_CAGE: StipulationModifiers(
        heat_multiplier=1.5,
        injury_chance_multiplier=1.8,
        stamina_cost_multiplier=1.3,
        damage_multiplier=1.2,
        star_rating_bonus=0.5,
        star_rating_penalty=0.5,
        production_cost=10000,
        fatigue_multiplier=1.3,
        min_turn_bonus=5,
        difficulty_rating=3,
        required_skills={"strength": 65, "stamina": 70, "psychology": 60},
        danger_profile=["Cage wall slam", "High fall from cage roof", "Door escape attempt"],
    ),

    MatchStipulation.LADDER: StipulationModifiers(
        heat_multiplier=2.0,
        injury_chance_multiplier=2.0,
        stamina_cost_multiplier=1.4,
        damage_multiplier=1.0,
        star_rating_bonus=1.0,
        star_rating_penalty=1.0,
        production_cost=5000,
        fatigue_multiplier=1.4,
        min_turn_bonus=3,
        difficulty_rating=4,
        required_skills={"agility": 70, "work_rate": 65},
        danger_profile=["Ladder suplex", "Dangerous ladder fall", "Crowd dive off ladder"],
    ),

    MatchStipulation.SUBMISSION_ONLY: StipulationModifiers(
        heat_multiplier=1.2,
        injury_chance_multiplier=1.1,
        stamina_cost_multiplier=1.8,
        damage_multiplier=0.5,
        star_rating_bonus=0.5,
        star_rating_penalty=0.75,
        production_cost=0,
        fatigue_multiplier=1.2,
        min_turn_bonus=5,
        difficulty_rating=3,
        required_skills={"work_rate": 75, "intelligence": 70},
        danger_profile=["Joint hyperextension", "Choke held too long"],
    ),
}

# Hype gates: stipulation → minimum company_hype required
HYPE_GATES: Dict[MatchStipulation, float] = {
    MatchStipulation.STEEL_CAGE: 100.0,
    MatchStipulation.LADDER: 80.0,
}


def get_modifiers(stipulation: MatchStipulation) -> StipulationModifiers:
    """Fetch the StipulationModifiers object for a given stipulation."""
    return STIPULATION_MODIFIERS[stipulation]


def validate_stipulation(
    stipulation: MatchStipulation, company_hype: Optional[float] = None
) -> None:
    """
    Raise ValueError if the company_hype is below the stipulation's gate.
    If company_hype is None, the gate check is silently skipped.
    """
    if company_hype is None:
        return
    if stipulation in HYPE_GATES and company_hype < HYPE_GATES[stipulation]:
        raise ValueError(
            f"{stipulation} requires company_hype >= {HYPE_GATES[stipulation]}. "
            f"Current: {company_hype}"
        )


def _resolve_stat(wrestler, key: str) -> float:
    """Resolve a string stat key to the wrestler's actual value."""
    mapping = {
        "strength":     lambda w: w.in_ring.strength,
        "agility":      lambda w: w.in_ring.agility,
        "stamina":      lambda w: w.in_ring.stamina,
        "work_rate":    lambda w: w.psychology.work_rate,
        "intelligence": lambda w: w.psychology.intelligence,
        "selling":      lambda w: w.psychology.selling,
        "psychology":   lambda w: (w.psychology.work_rate + w.psychology.intelligence + w.psychology.selling) / 3,
    }
    if key not in mapping:
        raise KeyError(f"Unknown stat key '{key}'. Valid keys: {list(mapping.keys())}")
    return float(mapping[key](wrestler))


def calculate_execution_score(wrestler, modifiers: StipulationModifiers) -> float:
    """
    Returns a raw_score (0.0–2.0+) representing how well this wrestler
    meets the stipulation's required skills.
    1.0 = meets requirements exactly.
    > 1.0 = exceeds requirements.
    < 1.0 = below requirements.
    Returns 1.0 if required_skills is empty.
    """
    if not modifiers.required_skills:
        return 1.0
    ratios = [
        _resolve_stat(wrestler, key) / required
        for key, required in modifiers.required_skills.items()
    ]
    return sum(ratios) / len(ratios)


def calculate_execution_modifier(raw_score: float, difficulty_rating: int) -> float:
    """Translate raw_score into a signed modifier for star rating adjustment."""
    return (raw_score - 1.0) * difficulty_rating * 0.1


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def resolve_danger_event(
    wrestlers: Dict[UUID, "Wrestler"],
    modifiers: StipulationModifiers,
    play_by_play: List[str],
    turn: int,
) -> Optional[UUID]:
    """
    Called every 3 turns. If a danger event fires, append narrative and
    trigger a targeted secondary injury roll. Returns injured wrestler's UUID or None.
    """
    if not modifiers.danger_profile or turn % 3 != 0:
        return None

    from src.engine.medical_engine import roll_for_injury

    event_name = random.choice(modifiers.danger_profile)
    target_id = random.choice(list(wrestlers.keys()))
    target = wrestlers[target_id]

    play_by_play.append(
        f"DANGER: {target.name} caught in a '{event_name}'!"
    )

    # Secondary targeted injury roll
    injury = roll_for_injury(target)
    if injury:
        target.injury_status = injury
        play_by_play.append(
            f"CRITICAL: {target.name} has been hurt — {injury.name}!"
        )
        return target_id

    return None
