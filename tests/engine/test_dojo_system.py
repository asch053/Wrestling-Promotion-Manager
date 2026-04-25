import pytest
import random
from uuid import uuid4

from src.models.promotion.dojo import Dojo, DojoStyle, DojoManager
from src.models.wrestler.wrestler import WrestlerStyle, InRingSkill, Psychology, Backstage, Popularity, Wrestler
from src.models.promotion.company import Company
from src.models.promotion.event import Event, EventScale
from src.engine.talent_generator import generate_class, STYLE_MAP, _roll_style, _generate_rookie
from src.engine.dojo_engine import (
    check_capacity, process_weekly_training, award_graduate_xp, calculate_dojo_maintenance
)


@pytest.fixture
def lucha_dojo():
    return Dojo(
        name="Escuela Lucha",
        style=DojoStyle.LUCHA,
        prestige_stars=2,
        equipment_level=3,
        appeal=70,
        manager=DojoManager(name="El Maestro", scouting_skill=80, training_skill=80),
    )

@pytest.fixture
def strong_dojo():
    return Dojo(
        name="Iron Forge Dojo",
        style=DojoStyle.STRONG_STYLE,
        prestige_stars=1,
        equipment_level=2,
        appeal=50,
        manager=DojoManager(name="Coach Steel", scouting_skill=60, training_skill=60),
    )


# --- Model Tests ---

def test_wrestler_style_enum_default():
    """Existing wrestlers get style=None — no existing tests break."""
    w = Wrestler(
        name="Veteran",
        in_ring=InRingSkill(strength=70, agility=70, stamina=70),
        psychology=Psychology(work_rate=70, selling=70),
        backstage=Backstage(ego=50, professionalism=70),
    )
    assert w.style is None

def test_dojo_model_defaults(lucha_dojo):
    assert lucha_dojo.name == "Escuela Lucha"
    assert lucha_dojo.style == DojoStyle.LUCHA
    assert lucha_dojo.prestige_stars == 2
    assert lucha_dojo.graduates == []
    assert lucha_dojo.students == []

def test_dojo_style_serialization():
    assert DojoStyle.LUCHA == "LUCHA"
    assert WrestlerStyle.HIGH_FLYER == "HIGH_FLYER"


# --- Capacity Tests ---

def test_capacity_formula(lucha_dojo):
    # prestige_stars=2, equipment_level=3 → capacity = (2*2) + 3 = 7
    assert check_capacity(lucha_dojo) is True
    
def test_capacity_min():
    dojo = Dojo(
        name="Small Gym",
        style=DojoStyle.BRAWLER,
        prestige_stars=0,
        equipment_level=1,
        manager=DojoManager(name="Trainer", scouting_skill=50, training_skill=50),
    )
    # capacity = (0*2) + 1 = 1
    for _ in range(1):
        dojo.students.append(Wrestler(
            name="Student",
            in_ring=InRingSkill(strength=40, agility=40, stamina=40),
            psychology=Psychology(work_rate=40, selling=40),
            backstage=Backstage(ego=40, professionalism=40),
        ))
    assert check_capacity(dojo) is False

def test_capacity_max():
    dojo = Dojo(
        name="Elite Academy",
        style=DojoStyle.TECHNICAL,
        prestige_stars=5,
        equipment_level=5,
        manager=DojoManager(name="Coach", scouting_skill=80, training_skill=80),
    )
    # capacity = (5*2) + 5 = 15
    for _ in range(14):
        dojo.students.append(Wrestler(
            name="Student",
            in_ring=InRingSkill(strength=40, agility=40, stamina=40),
            psychology=Psychology(work_rate=40, selling=40),
            backstage=Backstage(ego=40, professionalism=40),
        ))
    assert check_capacity(dojo) is True  # 14/15
    dojo.students.append(dojo.students[0])
    assert check_capacity(dojo) is False  # 15/15 = full


# --- Talent Generation Tests ---

def test_generate_class_size(lucha_dojo):
    for _ in range(10):
        cls = generate_class(lucha_dojo)
        assert 1 <= len(cls) <= 3

def test_generate_class_wrestler_style_bias(lucha_dojo):
    """Over many trials, LUCHA dojo should produce mostly HIGH_FLYERs."""
    all_rookies = []
    for _ in range(30):
        all_rookies.extend(generate_class(lucha_dojo))
    
    high_flyers = [r for r in all_rookies if r.style == WrestlerStyle.HIGH_FLYER]
    # 80% rule — should be well above 50%
    assert len(high_flyers) / len(all_rookies) > 0.5

def test_scouting_skill_baseline(strong_dojo):
    """High scouting skill should produce rookies with higher starting stats."""
    strong_dojo.manager.scouting_skill = 100
    rookies = []
    for _ in range(20):
        rookies.extend(generate_class(strong_dojo))
    
    avg_strength = sum(r.in_ring.strength for r in rookies) / len(rookies)
    # base=randint(30,50)+20 = 50-70, then +15 bias = 65-85 avg for strength
    assert avg_strength > 55

def test_style_bias_produces_distinct_archetypes():
    """A LUCHA Dojo should have higher agility than a STRONG_STYLE Dojo on average."""
    lucha = Dojo(
        name="Lucha Academy",
        style=DojoStyle.LUCHA,
        prestige_stars=2,
        equipment_level=3,
        manager=DojoManager(name="Maestro", scouting_skill=80, training_skill=80),
    )
    strong = Dojo(
        name="Power Gym",
        style=DojoStyle.STRONG_STYLE,
        prestige_stars=2,
        equipment_level=3,
        manager=DojoManager(name="Coach", scouting_skill=80, training_skill=80),
    )
    
    lucha_rookies = [r for _ in range(20) for r in generate_class(lucha)]
    strong_rookies = [r for _ in range(20) for r in generate_class(strong)]
    
    avg_lucha_agility = sum(r.in_ring.agility for r in lucha_rookies) / len(lucha_rookies)
    avg_strong_agility = sum(r.in_ring.agility for r in strong_rookies) / len(strong_rookies)
    
    avg_strong_strength = sum(r.in_ring.strength for r in strong_rookies) / len(strong_rookies)
    avg_lucha_strength = sum(r.in_ring.strength for r in lucha_rookies) / len(lucha_rookies)
    
    assert avg_lucha_agility > avg_strong_agility
    assert avg_strong_strength > avg_lucha_strength


# --- Training Tests ---

def test_weekly_training_growth(lucha_dojo):
    """training_skill=80, equipment=3 → gain = int(round(8.0+0.15)) = 8."""
    rookie = Wrestler(
        name="Student",
        in_ring=InRingSkill(strength=40, agility=40, stamina=40),
        psychology=Psychology(work_rate=40, selling=40),
        backstage=Backstage(ego=40, professionalism=40),
    )
    lucha_dojo.students = [rookie]
    
    initial_agility = rookie.in_ring.agility
    process_weekly_training(lucha_dojo)
    
    # LUCHA trains agility — should have increased
    assert rookie.in_ring.agility > initial_agility

def test_weekly_training_max_stats(lucha_dojo):
    """Stats should not exceed 100 after training."""
    rookie = Wrestler(
        name="Student",
        in_ring=InRingSkill(strength=99, agility=99, stamina=99),
        psychology=Psychology(work_rate=99, selling=99),
        backstage=Backstage(ego=99, professionalism=99),
    )
    lucha_dojo.students = [rookie]
    process_weekly_training(lucha_dojo)
    assert rookie.in_ring.agility <= 100

def test_training_targets_correct_stats(strong_dojo):
    """STRONG_STYLE should grow Strength, not Agility."""
    rookie = Wrestler(
        name="Student",
        in_ring=InRingSkill(strength=40, agility=40, stamina=40),
        psychology=Psychology(work_rate=40, selling=40),
        backstage=Backstage(ego=40, professionalism=40),
    )
    strong_dojo.students = [rookie]
    initial_agility = rookie.in_ring.agility
    initial_strength = rookie.in_ring.strength
    
    process_weekly_training(strong_dojo)
    
    assert rookie.in_ring.strength > initial_strength  # grew
    assert rookie.in_ring.agility == initial_agility   # untouched

def test_training_empty_dojo(lucha_dojo):
    """Training with 0 students should not raise errors."""
    lucha_dojo.students = []
    process_weekly_training(lucha_dojo)  # Should not raise


# --- XP & Prestige Tests ---

def test_match_win_xp(lucha_dojo):
    lucha_dojo.xp = 0
    award_graduate_xp(lucha_dojo, "MATCH_WIN")
    assert lucha_dojo.xp == 5

def test_title_win_xp(lucha_dojo):
    lucha_dojo.xp = 0
    award_graduate_xp(lucha_dojo, "TITLE_WIN")
    assert lucha_dojo.xp == 50

def test_star_promotion_threshold(strong_dojo):
    """100 match wins (500 XP) should promote from 1 star to 2 stars."""
    strong_dojo.prestige_stars = 1
    strong_dojo.xp = 0
    for _ in range(100):
        award_graduate_xp(strong_dojo, "MATCH_WIN")
    assert strong_dojo.prestige_stars == 2

def test_star_capped_at_5():
    dojo = Dojo(
        name="Legend Dojo",
        style=DojoStyle.TECHNICAL,
        prestige_stars=5,
        equipment_level=5,
        manager=DojoManager(name="Legend", scouting_skill=100, training_skill=100),
    )
    dojo.xp = 99999
    award_graduate_xp(dojo, "TITLE_WIN")
    assert dojo.prestige_stars == 5  # Capped


# --- Financial Tests ---

def test_dojo_maintenance_formula(lucha_dojo):
    # equipment_level=3, prestige_stars=2 → (3*1000) + (2*500) = 4000
    assert calculate_dojo_maintenance(lucha_dojo) == 4000

def test_three_dojos_total_maintenance():
    d1 = Dojo(name="D1", style=DojoStyle.LUCHA, prestige_stars=2, equipment_level=3,
              manager=DojoManager(name="M", scouting_skill=50, training_skill=50))
    d2 = Dojo(name="D2", style=DojoStyle.TECHNICAL, prestige_stars=1, equipment_level=1,
              manager=DojoManager(name="M", scouting_skill=50, training_skill=50))
    d3 = Dojo(name="D3", style=DojoStyle.STRONG_STYLE, prestige_stars=5, equipment_level=5,
              manager=DojoManager(name="M", scouting_skill=50, training_skill=50))
    
    total = sum(calculate_dojo_maintenance(d) for d in [d1, d2, d3])
    # d1=(3*1000)+(2*500)=4000, d2=(1*1000)+(1*500)=1500, d3=(5*1000)+(5*500)=7500
    assert total == 4000 + 1500 + 7500

def test_no_dojos_zero_expense():
    company = Company(name="AWF")
    total = sum(calculate_dojo_maintenance(d) for d in company.dojos)
    assert total == 0
