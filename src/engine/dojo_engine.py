from src.models.promotion.dojo import Dojo
from src.engine.talent_generator import STYLE_BIAS_TRAINING, _clamp


def check_capacity(dojo: Dojo) -> bool:
    """Return True if the Dojo can accept another student."""
    max_capacity = (dojo.prestige_stars * 2) + dojo.equipment_level
    return len(dojo.students) < max_capacity


def process_weekly_training(dojo: Dojo, current_day: int):
    """
    Apply weekly stat growth to all Dojo students.
    Growth targets are biased by the Dojo's style.
    """
    if current_day != 7:
        raise PermissionError("Training can only be processed on Day 7.")
    stat_increase = (dojo.manager.training_skill * 0.1) + (dojo.equipment_level * 0.05)
    gain = int(round(stat_increase))

    if gain == 0:
        return

    training_targets = STYLE_BIAS_TRAINING[dojo.style]

    for wrestler in dojo.students:
        for model_attr, stat_name in training_targets:
            model = getattr(wrestler, model_attr)
            current = getattr(model, stat_name)
            setattr(model, stat_name, _clamp(current + gain))


def award_graduate_xp(dojo: Dojo, event_type: str):
    """
    Award XP to the Dojo when a graduate succeeds on the main roster.
    event_type: "MATCH_WIN" (+5 XP) or "TITLE_WIN" (+50 XP).
    Automatically promotes prestige_stars when threshold is met.
    """
    xp_rewards = {
        "MATCH_WIN":  5,
        "TITLE_WIN":  50,
    }
    dojo.xp += xp_rewards.get(event_type, 0)

    # Each prestige_stars upgrade requires (prestige_stars * 500) total XP
    # e.g. 1→2 star at 500 XP, 2→3 at 1000 XP, etc.
    next_star_threshold = dojo.prestige_stars * 500
    if dojo.prestige_stars < 5 and dojo.xp >= next_star_threshold:
        dojo.prestige_stars += 1


def calculate_dojo_maintenance(dojo: Dojo) -> int:
    """Return the weekly maintenance cost for a single Dojo."""
    return (dojo.equipment_level * 1000) + (dojo.prestige_stars * 500)
