import random
from typing import List, Optional
from src.models.wrestler.wrestler import Wrestler
from src.models.wrestler.injury import Injury, InjuryType
from src.models.promotion.company import Company

INJURY_LOOKUP_TABLE = [
    {"name": "Sprained Ankle", "type": InjuryType.MINOR, "min_weeks": 1, "max_weeks": 2, "stat": "agility"},
    {"name": "Bruised Ribs", "type": InjuryType.MINOR, "min_weeks": 1, "max_weeks": 3, "stat": "stamina"},
    {"name": "Strained Back", "type": InjuryType.MINOR, "min_weeks": 2, "max_weeks": 4, "stat": "strength"},
    {"name": "Concussion", "type": InjuryType.MINOR, "min_weeks": 2, "max_weeks": 4, "stat": "psychology"},
    {"name": "Broken Arm", "type": InjuryType.MAJOR, "min_weeks": 4, "max_weeks": 8, "stat": None},
    {"name": "Torn ACL", "type": InjuryType.MAJOR, "min_weeks": 12, "max_weeks": 24, "stat": None},
    {"name": "Neck Injury", "type": InjuryType.MAJOR, "min_weeks": 8, "max_weeks": 16, "stat": None},
    {"name": "Separated Shoulder", "type": InjuryType.MAJOR, "min_weeks": 6, "max_weeks": 12, "stat": None},
]

def calculate_injury_chance(wrestler: Wrestler) -> float:
    base_rate = 0.02
    fatigue_factor = 1.0 + (wrestler.fatigue / 100.0)
    agility_factor = 1.0 - (wrestler.in_ring.agility / 200.0)
    return base_rate * fatigue_factor * agility_factor

def roll_for_injury(wrestler: Wrestler) -> Optional[Injury]:
    chance = calculate_injury_chance(wrestler)
    if random.random() < chance:
        # Determine severity: 70% Minor, 30% Major
        is_major = random.random() < 0.3
        target_type = InjuryType.MAJOR if is_major else InjuryType.MINOR
        
        possible_injuries = [i for i in INJURY_LOOKUP_TABLE if i["type"] == target_type]
        injury_data = random.choice(possible_injuries)
        
        weeks = random.randint(injury_data["min_weeks"], injury_data["max_weeks"])
        
        return Injury(
            name=injury_data["name"],
            injury_type=injury_data["type"],
            weeks_remaining=float(weeks),
            affected_stat=injury_data["stat"],
            is_sidelined=(target_type == InjuryType.MAJOR)
        )
    return None

def process_weekly_recovery(company: Company):
    recovery_boost = 1.0 + (company.medical_staff_level * 0.2)
    
    for wrestler in company.current_roster:
        # 1. Fatigue Recovery
        wrestler.fatigue = max(0, wrestler.fatigue - int(10 * recovery_boost))
        
        # 2. Injury Healing
        if wrestler.injury_status:
            wrestler.injury_status.weeks_remaining -= (1.0 * recovery_boost)
            if wrestler.injury_status.weeks_remaining <= 0:
                wrestler.injury_status = None
                
def get_effective_stat(wrestler: Wrestler, stat_name: str) -> int:
    is_physical = stat_name in ["strength", "agility", "stamina"]
    
    # Get base stat
    if hasattr(wrestler.in_ring, stat_name):
        base_stat = getattr(wrestler.in_ring, stat_name)
    elif hasattr(wrestler.psychology, stat_name):
        base_stat = getattr(wrestler.psychology, stat_name)
    else:
        return 0
    
    if wrestler.injury_status and wrestler.injury_status.injury_type == InjuryType.MINOR:
        if is_physical:
            return int(base_stat * 0.8)
        
        # Check if the stat is in the psychology category
        is_psychology = stat_name in ["work_rate", "selling", "intelligence"]
        if is_psychology and wrestler.injury_status.affected_stat == "psychology":
            return int(base_stat * 0.8)
            
        if wrestler.injury_status.affected_stat == stat_name:
            return int(base_stat * 0.8)
            
    return base_stat
