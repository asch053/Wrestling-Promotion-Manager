import pytest
from uuid import uuid4
from src.models.promotion.championship import Championship, ChampionshipType, ChampionshipTier, TitleReign
from src.models.promotion.company import Company
from src.models.wrestler.wrestler import Wrestler, InRingSkill, Psychology, Backstage, Popularity
from src.models.wrestler.contract import Contract
from src.models.promotion.booking.booking_sheet import BookingSheet, MatchType, ScriptingStyle
from src.models.wrestler.moveset import Move, MoveType
from src.engine.championship_manager import (
    award_title, vacate_title, retire_title, unretire_title,
    update_prestige, calculate_saturation_penalty, check_hierarchy_violation,
    wrestler_holds_title, wrestler_holds_world_title
)
from src.engine.morale_engine import calculate_morale_shift
from src.engine.match_simulator import simulate_match

@pytest.fixture
def title_setup():
    champ_id = uuid4()
    w1_id = uuid4()
    
    belt = Championship(
        id=champ_id,
        name="World Heavyweight Championship",
        prestige=50,
        championship_type=ChampionshipType.SINGLES,
        tier=ChampionshipTier.WORLD
    )
    
    w1 = Wrestler(
        name="Champion",
        in_ring=InRingSkill(strength=80, agility=80, stamina=100),
        psychology=Psychology(work_rate=80, selling=80),
        backstage=Backstage(ego=80, professionalism=80),
        popularity=Popularity(hype=90, heat=0, pop=90),
        contract=Contract(appearance_fee=5000, weekly_salary=5000, merch_cut_percentage=0.5)
    )
    
    return champ_id, belt, w1_id, w1

def test_championship_creation(title_setup):
    _, belt, _, _ = title_setup
    assert belt.name == "World Heavyweight Championship"
    assert belt.prestige == 50
    assert belt.championship_type == ChampionshipType.SINGLES
    assert belt.tier == ChampionshipTier.WORLD
    assert belt.is_active is True
    assert belt.current_holder is None
    assert len(belt.title_history) == 0

def test_title_reign_tracking(title_setup):
    _, belt, w1_id, w1 = title_setup
    
    award_title(belt, w1_id, w1.name, "SummerSlam")
    assert belt.current_holder == w1_id
    assert len(belt.title_history) == 1
    assert belt.title_history[0].holder_name == "Champion"
    assert belt.title_history[0].start_event == "SummerSlam"
    
    vacate_title(belt, "Raw")
    assert belt.current_holder is None
    assert belt.title_history[0].end_event == "Raw"

def test_prestige_5_star_defense(title_setup):
    _, belt, w1_id, w1 = title_setup
    award_title(belt, w1_id, w1.name, "WrestleMania")
    
    update_prestige(belt, 5.0)
    assert belt.prestige == 60  # 50 + 10
    assert belt.title_history[-1].defenses == 1

def test_prestige_1_star_tank(title_setup):
    _, belt, w1_id, w1 = title_setup
    award_title(belt, w1_id, w1.name, "WrestleMania")
    
    update_prestige(belt, 1.0)
    assert belt.prestige == 40  # 50 - 10
    assert belt.title_history[-1].defenses == 1

def test_saturation_penalty():
    company = Company(name="AWF")
    # Add 6 active titles
    for i in range(6):
        company.championships.append(Championship(
            id=uuid4(),
            name=f"Belt {i}",
            championship_type=ChampionshipType.SINGLES,
            tier=ChampionshipTier.MID_CARD
        ))
    
    penalty = calculate_saturation_penalty(company)
    # (6 - 4) * 0.05 * excitement
    assert penalty > 0
    
    # With 4 titles, penalty should be 0
    company2 = Company(name="AWF")
    for i in range(4):
        company2.championships.append(Championship(
            id=uuid4(),
            name=f"Belt {i}",
            championship_type=ChampionshipType.SINGLES,
            tier=ChampionshipTier.MID_CARD
        ))
    assert calculate_saturation_penalty(company2) == 0

def test_retirement_reduces_saturation():
    company = Company(name="AWF")
    belts = []
    for i in range(6):
        b = Championship(
            id=uuid4(), name=f"Belt {i}",
            championship_type=ChampionshipType.SINGLES,
            tier=ChampionshipTier.MID_CARD
        )
        company.championships.append(b)
        belts.append(b)
    
    penalty_before = calculate_saturation_penalty(company)
    retire_title(belts[0])
    penalty_after = calculate_saturation_penalty(company)
    
    assert penalty_after < penalty_before

def test_unretire_preserves_prestige(title_setup):
    _, belt, w1_id, w1 = title_setup
    award_title(belt, w1_id, w1.name, "Mania")
    update_prestige(belt, 5.0)  # prestige = 60
    
    retire_title(belt, "Farewell")
    assert belt.is_active is False
    assert belt.prestige == 60
    assert len(belt.title_history) == 1
    
    unretire_title(belt)
    assert belt.is_active is True
    assert belt.prestige == 60  # Full historical value preserved

def test_hierarchy_violation(title_setup):
    _, belt, _, _ = title_setup
    
    low_hype = Wrestler(
        name="Rookie",
        in_ring=InRingSkill(strength=50, agility=50, stamina=50),
        psychology=Psychology(work_rate=50, selling=50),
        backstage=Backstage(ego=50, professionalism=50),
        popularity=Popularity(hype=30, heat=0, pop=30)
    )
    assert check_hierarchy_violation(low_hype, belt) is True
    
    high_hype = Wrestler(
        name="Star",
        in_ring=InRingSkill(strength=50, agility=50, stamina=50),
        psychology=Psychology(work_rate=50, selling=50),
        backstage=Backstage(ego=50, professionalism=50),
        popularity=Popularity(hype=80, heat=0, pop=80)
    )
    assert check_hierarchy_violation(high_hype, belt) is False

def test_hunger_titleless_ego(title_setup):
    _, belt, w1_id, w1 = title_setup
    company = Company(name="AWF", current_roster=[w1], championships=[belt])
    
    # w1 has ego=80, hype=90, no title -> should lose 5 + 5 = 10
    shift = calculate_morale_shift(
        w1, was_booked=True, won=True, company=company,
        wrestler_id=w1_id, championships=company.championships
    )
    # +5 (win) - 5 (no title, ego > 70) - 5 (no WORLD, hype > 80) = -5
    assert shift == -5

def test_hunger_champion_no_penalty(title_setup):
    _, belt, w1_id, w1 = title_setup
    award_title(belt, w1_id, w1.name, "Mania")
    company = Company(name="AWF", current_roster=[w1], championships=[belt])
    
    shift = calculate_morale_shift(
        w1, was_booked=True, won=True, company=company,
        wrestler_id=w1_id, championships=company.championships
    )
    # +5 (win), no hunger penalty because they hold a WORLD title
    assert shift == 5

def test_world_title_boosts_hype(title_setup):
    _, belt, w1_id, w1 = title_setup
    company_without = Company(name="AWF", current_roster=[w1])
    company_with = Company(name="AWF", current_roster=[w1], championships=[belt])
    
    hype_without = company_without.calculate_current_hype()
    hype_with = company_with.calculate_current_hype()
    
    # WORLD title adds prestige * 2 = 50 * 2 = 100
    assert hype_with == hype_without + 100

def test_simulator_prestige_update(title_setup):
    champ_id, belt, w1_id, w1 = title_setup
    w2_id = uuid4()
    w2 = Wrestler(
        name="Challenger",
        in_ring=InRingSkill(strength=80, agility=80, stamina=100),
        psychology=Psychology(work_rate=80, selling=80),
        backstage=Backstage(ego=50, professionalism=80),
        popularity=Popularity(hype=30, heat=0, pop=30), # Low hype violation
        morale=100
    )
    roster_dict = {w1_id: w1, w2_id: w2}
    
    m1_id = uuid4()
    move = Move(name="Slam", selling_burden=10, stamina_cost=5, heat_generation=20, move_type=MoveType.GRAPPLE)
    moves = {m1_id: move}
    w1.moveset = {m1_id}
    w2.moveset = {m1_id}
    
    w1.morale = 100
    w1.popularity.hype = 90 # Champ is fine
    
    booking = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[w1_id], [w2_id]],
        scripting_style=ScriptingStyle.CALLED_IN_RING,
        designated_winner=w1_id,
        championship_id=champ_id
    )
    
    initial_prestige = belt.prestige
    championships = {champ_id: belt}
    report = simulate_match(booking, roster_dict, moves, championships=championships)
    
    # Champ (90 hype) = no penalty
    # Challenger (30 hype) = -5 penalty
    # star_rating should be around 5.0
    # base delta = (5.0 - 3.0) * 5 = 10
    # total delta = 10 - 5 = 5
    expected_delta = int(round((report.star_rating - 3.0) * 5)) - 5
    assert report.prestige_delta == expected_delta
    assert belt.prestige == initial_prestige + expected_delta
    assert "devaluing the belt" in " ".join(report.play_by_play)
