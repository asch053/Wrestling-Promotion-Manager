import random
from typing import List
from uuid import uuid4

from src.models.promotion.dojo import Dojo, DojoStyle
from src.models.wrestler.wrestler import (
    Wrestler, WrestlerStyle, InRingSkill, Psychology, Backstage, Popularity
)

# --- Style Map: DojoStyle → WrestlerStyle (80% probability) ---
STYLE_MAP: dict = {
    DojoStyle.STRONG_STYLE: WrestlerStyle.HEAVY_HITTER,
    DojoStyle.TECHNICAL:    WrestlerStyle.GRAPPLER,
    DojoStyle.LUCHA:        WrestlerStyle.HIGH_FLYER,
    DojoStyle.BRAWLER:      WrestlerStyle.BRAWLER,
    DojoStyle.SHOWMAN:      WrestlerStyle.SHOWMAN,
}

# --- Style Bias: stat paths boosted +15 at generation ---
# Each entry is (model_attribute, stat_name) tuples
STYLE_BIAS_GENERATION: dict = {
    DojoStyle.STRONG_STYLE: [("in_ring", "strength"), ("in_ring", "stamina")],
    DojoStyle.TECHNICAL:    [("psychology", "work_rate"), ("psychology", "intelligence")],
    DojoStyle.LUCHA:        [("in_ring", "agility"), ("psychology", "selling")],
    DojoStyle.BRAWLER:      [("in_ring", "strength"), ("backstage", "ego")],
    DojoStyle.SHOWMAN:      [("psychology", "selling"), ("psychology", "work_rate")],
}

# --- Style Bias: stats grown weekly during training ---
STYLE_BIAS_TRAINING: dict = {
    DojoStyle.STRONG_STYLE: [("in_ring", "strength"), ("in_ring", "stamina")],
    DojoStyle.TECHNICAL:    [("psychology", "work_rate"), ("psychology", "intelligence")],
    DojoStyle.LUCHA:        [("in_ring", "agility"), ("psychology", "selling")],
    DojoStyle.BRAWLER:      [("in_ring", "strength"), ("backstage", "ego")],
    DojoStyle.SHOWMAN:      [("psychology", "selling"), ("in_ring", "agility")],
}


def _roll_style(dojo_style: DojoStyle) -> WrestlerStyle:
    """80% chance of matching the Dojo's style, 20% random surprise."""
    if random.random() < 0.80:
        return STYLE_MAP[dojo_style]
    return random.choice(list(WrestlerStyle))


def _clamp(value: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, value))


def _apply_bias(stats: dict, bias_targets: list, bonus: int = 15) -> dict:
    """Apply a flat bonus to the specified (model, stat) pairs."""
    for model_key, stat_key in bias_targets:
        if model_key in stats and stat_key in stats[model_key]:
            stats[model_key][stat_key] = _clamp(stats[model_key][stat_key] + bonus)
    return stats


def _generate_rookie(dojo: Dojo) -> Wrestler:
    """Generate a single rookie wrestler biased by the Dojo's style and manager."""
    base = lambda: _clamp(random.randint(30, 50) + int(dojo.manager.scouting_skill * 0.2))

    raw_stats = {
        "in_ring":   {"strength": base(), "agility": base(), "stamina": base()},
        "psychology": {"work_rate": base(), "selling": base(), "intelligence": base()},
        "backstage":  {"ego": base(), "professionalism": base()},
    }

    # Apply style generation bias (+15 to signature stats)
    raw_stats = _apply_bias(raw_stats, STYLE_BIAS_GENERATION[dojo.style])

    wrestler_style = _roll_style(dojo.style)

    return Wrestler(
        name=f"Rookie-{str(uuid4())[:8]}",
        in_ring=InRingSkill(**raw_stats["in_ring"]),
        psychology=Psychology(**raw_stats["psychology"]),
        backstage=Backstage(**raw_stats["backstage"]),
        popularity=Popularity(hype=20, heat=10, pop=10),
        style=wrestler_style,
        morale=60,
    )


def generate_class(dojo: Dojo) -> List[Wrestler]:
    """
    Generate a class of 1-3 rookies for the Dojo.
    Should only be called when game_turn % 4 == 0 (caller's responsibility).
    """
    class_size = random.randint(1, 3)
    return [_generate_rookie(dojo) for _ in range(class_size)]
