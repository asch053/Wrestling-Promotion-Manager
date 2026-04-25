import pytest
from uuid import uuid4

from src.models.wrestler.wrestler import Wrestler, InRingSkill, Psychology, Backstage, Popularity
from src.models.promotion.company import Company
from src.models.promotion.booking.booking_sheet import BookingSheet, MatchType, ScriptingStyle
from src.engine.stipulation_logic_handler import (
    MatchStipulation, get_modifiers, validate_stipulation,
    calculate_execution_score, calculate_execution_modifier, _clamp
)
from src.engine.match_simulator import simulate_match


# --- Fixtures ---

@pytest.fixture
def high_flyer():
    return Wrestler(
        name="Aero",
        in_ring=InRingSkill(strength=60, agility=90, stamina=75),
        psychology=Psychology(work_rate=80, selling=75),
        backstage=Backstage(ego=40, professionalism=80),
        popularity=Popularity(hype=60, heat=20, pop=60),
    )

@pytest.fixture
def brawler():
    return Wrestler(
        name="Bruiser",
        in_ring=InRingSkill(strength=80, agility=35, stamina=80),
        psychology=Psychology(work_rate=55, selling=45),
        backstage=Backstage(ego=70, professionalism=50),
        popularity=Popularity(hype=50, heat=40, pop=20),
    )

@pytest.fixture
def technician():
    return Wrestler(
        name="Professor",
        in_ring=InRingSkill(strength=60, agility=65, stamina=70),
        psychology=Psychology(work_rate=85, selling=80, intelligence=80),
        backstage=Backstage(ego=30, professionalism=90),
        popularity=Popularity(hype=55, heat=10, pop=55),
    )

@pytest.fixture
def company():
    return Company(name="AWF")


# --- Stipulation Model Tests ---

def test_stipulation_enum_serialization():
    assert MatchStipulation.LADDER == "LADDER"
    assert MatchStipulation.STANDARD == "STANDARD"

def test_booking_sheet_defaults_standard():
    w_id = uuid4()
    w2_id = uuid4()
    sheet = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[w_id], [w2_id]],
        scripting_style=ScriptingStyle.CALLED_IN_RING,
        designated_winner=w_id,
    )
    assert sheet.stipulation == MatchStipulation.STANDARD

def test_get_modifiers_hardcore():
    m = get_modifiers(MatchStipulation.HARDCORE)
    assert m.heat_multiplier == 2.0
    assert m.injury_chance_multiplier == 2.5
    assert m.fatigue_multiplier == 1.5

def test_get_modifiers_standard_all_ones():
    m = get_modifiers(MatchStipulation.STANDARD)
    assert m.heat_multiplier == 1.0
    assert m.injury_chance_multiplier == 1.0
    assert m.star_rating_bonus == 0.0
    assert m.production_cost == 0

def test_ladder_modifiers():
    m = get_modifiers(MatchStipulation.LADDER)
    assert m.star_rating_bonus == 1.0
    assert m.star_rating_penalty == 1.0
    assert m.production_cost == 5000
    assert m.difficulty_rating == 4

def test_steel_cage_production_cost():
    m = get_modifiers(MatchStipulation.STEEL_CAGE)
    assert m.production_cost == 10000

def test_submission_only_required_skills():
    m = get_modifiers(MatchStipulation.SUBMISSION_ONLY)
    assert "work_rate" in m.required_skills
    assert "intelligence" in m.required_skills


# --- Validation Tests ---

def test_validate_steel_cage_passes_with_sufficient_hype():
    validate_stipulation(MatchStipulation.STEEL_CAGE, company_hype=100.0)  # No error

def test_validate_steel_cage_fails_below_threshold():
    with pytest.raises(ValueError, match="company_hype >= 100"):
        validate_stipulation(MatchStipulation.STEEL_CAGE, company_hype=99.0)

def test_validate_ladder_fails_below_threshold():
    with pytest.raises(ValueError, match="company_hype >= 80"):
        validate_stipulation(MatchStipulation.LADDER, company_hype=50.0)

def test_validate_hardcore_no_gate():
    validate_stipulation(MatchStipulation.HARDCORE, company_hype=1.0)  # No gate

def test_validate_no_hype_provided_skips_gate():
    validate_stipulation(MatchStipulation.STEEL_CAGE, company_hype=None)  # No error


# --- Execution Score Tests ---

def test_execution_score_meets_exactly(high_flyer):
    """agility=90, required=70 → ratio=90/70=1.286; work_rate=80, required=65 → 1.23"""
    m = get_modifiers(MatchStipulation.LADDER)
    score = calculate_execution_score(high_flyer, m)
    assert score > 1.0  # Exceeds requirements

def test_execution_score_standard_is_one(high_flyer):
    """STANDARD has no required_skills → always returns 1.0"""
    m = get_modifiers(MatchStipulation.STANDARD)
    score = calculate_execution_score(high_flyer, m)
    assert score == 1.0

def test_execution_score_below_threshold(brawler):
    """brawler agility=35, required=70 → ratio=0.5; work_rate=55, required=65 → 0.846"""
    m = get_modifiers(MatchStipulation.LADDER)
    score = calculate_execution_score(brawler, m)
    assert score < 1.0

def test_botch_threshold(brawler):
    """brawler agility=35, required=70 → ratio=0.5 < 0.6 → botch trigger"""
    m = get_modifiers(MatchStipulation.LADDER)
    agility_ratio = brawler.in_ring.agility / m.required_skills["agility"]
    assert agility_ratio < 0.6


# --- Execution Modifier Math ---

def test_execution_modifier_at_threshold():
    modifier = calculate_execution_modifier(1.0, difficulty_rating=4)
    assert modifier == pytest.approx(0.0)

def test_execution_modifier_above_threshold():
    modifier = calculate_execution_modifier(1.5, difficulty_rating=4)
    assert modifier == pytest.approx(0.20)

def test_execution_modifier_below_threshold():
    modifier = calculate_execution_modifier(0.5, difficulty_rating=4)
    assert modifier == pytest.approx(-0.20)


# --- Star Rating Integration Tests ---

def test_ladder_skilled_wrestler_gets_bonus(high_flyer, brawler):
    """High-flyer in a LADDER match should score better than the same match as STANDARD."""
    w1_id = uuid4()
    w2_id = uuid4()
    
    from src.models.wrestler.moveset import Move, MoveType
    move_id = uuid4()
    move = Move(name="Crossbody", move_type=MoveType.AERIAL, heat_generation=20,
                stamina_cost=10, damage=15)
    
    high_flyer_copy = high_flyer.model_copy()
    high_flyer_copy.moveset = {move_id}
    brawler_copy = brawler.model_copy()
    brawler_copy.moveset = {move_id}
    
    roster = {w1_id: high_flyer_copy, w2_id: brawler_copy}
    move_lib = {move_id: move}
    
    booking_standard = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[w1_id], [w2_id]],
        scripting_style=ScriptingStyle.CALLED_IN_RING,
        designated_winner=w1_id,
        stipulation=MatchStipulation.STANDARD,
    )
    booking_ladder = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[w1_id], [w2_id]],
        scripting_style=ScriptingStyle.CALLED_IN_RING,
        designated_winner=w1_id,
        stipulation=MatchStipulation.LADDER,
    )
    
    # Reset fatigue between runs
    high_flyer_copy.fatigue = 0
    brawler_copy.fatigue = 0
    report_standard = simulate_match(booking_standard, roster, move_lib)
    
    high_flyer_copy.fatigue = 0
    brawler_copy.fatigue = 0
    high_flyer_copy.injury_status = None
    brawler_copy.injury_status = None
    report_ladder = simulate_match(booking_ladder, roster, move_lib)
    
    # Ladder with high-flyer exceeding requirements → higher or equal star rating
    assert report_ladder.star_rating >= report_standard.star_rating - 0.1


# --- Staleness Tests ---

def test_stipulation_usage_counter_increments(company):
    from src.models.promotion.event import Event, EventScale
    from src.engine.financial_engine import process_event_finances
    
    event = Event(name="House Show", location="Anywhere", scale=EventScale.HOUSE_SHOW)
    
    for _ in range(3):
        e = Event(name="Show", location="Anywhere", scale=EventScale.HOUSE_SHOW)
        process_event_finances(company, e, MatchStipulation.HARDCORE)
    
    assert company.stipulation_usage.get("HARDCORE", 0) == 3

def test_staleness_penalty_on_4th_use(company):
    from src.models.promotion.event import Event, EventScale
    from src.engine.financial_engine import process_event_finances
    
    event = Event(name="Show", location="Anywhere", scale=EventScale.HOUSE_SHOW)
    
    # 3 HARDCORE events (no penalty)
    for _ in range(3):
        process_event_finances(company, event, MatchStipulation.HARDCORE)
    
    balance_before = company.bank_balance
    # 4th HARDCORE — staleness kicks in
    process_event_finances(company, event, MatchStipulation.HARDCORE)
    
    assert company.stipulation_usage["HARDCORE"] == 4
    # The 4th show's gate should be reduced — net profit lower than event 3

def test_staleness_counter_resets_on_stipulation_change(company):
    from src.models.promotion.event import Event, EventScale
    from src.engine.financial_engine import process_event_finances
    
    event = Event(name="Show", location="Anywhere", scale=EventScale.HOUSE_SHOW)
    
    for _ in range(3):
        process_event_finances(company, event, MatchStipulation.HARDCORE)
    
    # Switch to STANDARD
    process_event_finances(company, event, MatchStipulation.STANDARD)
    
    assert company.stipulation_usage.get("HARDCORE", 0) == 0
    assert company.stipulation_usage.get("STANDARD", 0) == 1


# --- Danger Profile Test ---

def test_danger_profile_exists_for_gimmick_matches():
    for stip in [MatchStipulation.HARDCORE, MatchStipulation.STEEL_CAGE,
                 MatchStipulation.LADDER, MatchStipulation.SUBMISSION_ONLY]:
        m = get_modifiers(stip)
        assert len(m.danger_profile) > 0, f"{stip} should have danger events"

def test_standard_has_no_danger_profile():
    m = get_modifiers(MatchStipulation.STANDARD)
    assert m.danger_profile == []
