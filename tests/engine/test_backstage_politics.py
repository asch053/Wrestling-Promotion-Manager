import pytest
import random
from uuid import uuid4
from src.models.wrestler.wrestler import Wrestler, KayfabeStatus, InRingSkill, Psychology, Backstage, Popularity
from src.models.wrestler.contract import Contract
from src.models.wrestler.moveset import Move, MoveType
from src.models.promotion.company import Company
from src.models.promotion.storyline import Storyline, PlannedOutcome
from src.models.promotion.booking.booking_sheet import BookingSheet, ScriptingStyle, MatchType
from src.models.promotion.booking.runsheet import Runsheet
from src.engine.morale_engine import calculate_morale_shift, apply_morale_shift, calculate_resign_difficulty
from src.engine.incident_generator import generate_incidents, apply_incident, Incident, IncidentType
from src.engine.match_simulator import simulate_match

@pytest.fixture
def roster():
    w1_id = uuid4()
    w2_id = uuid4()
    
    w1 = Wrestler(
        name="Star",
        in_ring=InRingSkill(strength=80, agility=80, stamina=100),
        psychology=Psychology(work_rate=80, selling=80),
        backstage=Backstage(ego=100, professionalism=80),
        popularity=Popularity(hype=90, heat=0, pop=90),
        contract=Contract(appearance_fee=5000, weekly_salary=5000, merch_cut_percentage=0.5),
        morale=50
    )
    
    w2 = Wrestler(
        name="Jobber",
        in_ring=InRingSkill(strength=50, agility=50, stamina=100),
        psychology=Psychology(work_rate=50, selling=50),
        backstage=Backstage(ego=20, professionalism=80),
        popularity=Popularity(hype=20, heat=0, pop=20),
        contract=Contract(appearance_fee=500, weekly_salary=500, merch_cut_percentage=0.05),
        morale=50
    )
    
    company = Company(name="AWF", current_roster=[w1, w2])
    roster_dict = {w1_id: w1, w2_id: w2}
    return w1_id, w1, w2_id, w2, company, roster_dict

def test_morale_win_boost(roster):
    _, w1, _, _, company, _ = roster
    shift = calculate_morale_shift(w1, was_booked=True, won=True, company=company)
    assert shift == 5

def test_morale_loss_ego_amplifier(roster):
    _, w1, _, _, company, _ = roster
    # w1 has 100 ego. Loss = -3 * (1 + 100/100) = -3 * 2 = -6
    shift = calculate_morale_shift(w1, was_booked=True, won=False, company=company)
    assert shift == -6

def test_morale_benched_decay(roster):
    _, _, _, w2, company, _ = roster
    # w2 has 20 ego. Benched = -5 * (1 + 20/100) = -5 * 1.2 = -6
    shift = calculate_morale_shift(w2, was_booked=False, won=False, company=company)
    assert shift == -6

def test_morale_push_storyline_boost(roster):
    w1_id, w1, w2_id, _, company, _ = roster
    s = Storyline(
        id=uuid4(),
        name="Push Star",
        participants=[w1_id, w2_id],
        planned_outcome=PlannedOutcome.PUSH_STAR,
        target_wrestler=w1_id
    )
    shift = calculate_morale_shift(w1, was_booked=True, won=True, company=company, storylines=[s])
    # +5 (win) + 10 (push) = +15
    assert shift == 15

def test_morale_financial_fairness(roster):
    _, w1, _, w2, company, _ = roster
    # w2 has lower hype (20) but let's give them a higher salary than w1
    w2.contract.weekly_salary = 10000  # Jobber paid more than the Star
    shift = calculate_morale_shift(w1, was_booked=True, won=True, company=company)
    # +5 (win) - 10 (unfair pay) = -5
    assert shift == -5

def test_morale_apply_clamp(roster):
    _, w1, _, _, _, _ = roster
    w1.morale = 5
    apply_morale_shift(w1, -20)
    assert w1.morale == 0  # Clamped at 0
    
    apply_morale_shift(w1, 200)
    assert w1.morale == 100  # Clamped at 100

def test_resign_difficulty(roster):
    _, w1, _, _, _, _ = roster
    w1.morale = 100
    assert calculate_resign_difficulty(w1) == 0.0
    
    w1.morale = 0
    assert calculate_resign_difficulty(w1) == 1.0
    
    w1.morale = 20
    assert calculate_resign_difficulty(w1) == 0.8

def test_incident_trigger_threshold(roster):
    _, w1, w2_id, w2, company, roster_dict = roster
    # w1 has ego=100, but prof=80 -> should NOT trigger (prof must be < 40)
    w1.morale = 10
    company.game_state.current_day = 6
    incidents = generate_incidents(company, roster_dict)
    assert len(incidents) == 0
    
    # Now make w1 meet all criteria
    w1.backstage.professionalism = 20
    w1.morale = 10
    random.seed(42)
    company.game_state.current_day = 6
    incidents = generate_incidents(company, roster_dict)
    assert len(incidents) == 1

def test_locker_room_poison(roster):
    w1_id, w1, w2_id, w2, company, roster_dict = roster
    # Set up faction
    faction_id = uuid4()
    w1.faction_id = faction_id
    w2.faction_id = faction_id
    
    incident = Incident(
        wrestler_id=w1_id,
        incident_type=IncidentType.LOCKER_ROOM_POISON,
        description="Poisoning the locker room"
    )
    
    initial_morale = w2.morale
    apply_incident(incident, company, roster_dict)
    assert w2.morale == initial_morale - 15

def test_public_shooting(roster):
    w1_id, w1, _, _, company, roster_dict = roster
    initial = company.base_excitement_modifier
    
    incident = Incident(
        wrestler_id=w1_id,
        incident_type=IncidentType.PUBLIC_SHOOTING,
        description="Public shooting"
    )
    
    apply_incident(incident, company, roster_dict)
    assert company.base_excitement_modifier == initial - 5

def test_refusal_to_lose(roster):
    w1_id, w1, w2_id, w2, _, roster_dict = roster
    
    m1_id = uuid4()
    move = Move(name="Slam", selling_burden=10, stamina_cost=5, heat_generation=20, move_type=MoveType.GRAPPLE)
    moves = {m1_id: move}
    w1.moveset = {m1_id}
    w2.moveset = {m1_id}
    
    # Book w1 to win, but w2 has a REFUSAL_TO_LOSE
    booking = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[w1_id], [w2_id]],
        scripting_style=ScriptingStyle.CALLED_IN_RING,
        designated_winner=w1_id
    )
    
    incident = Incident(
        wrestler_id=w2_id,
        incident_type=IncidentType.REFUSAL_TO_LOSE,
        description="Refusing to lose"
    )
    
    report = simulate_match(booking, roster_dict, moves, active_incidents=[incident])
    
    # The winner should have been overridden
    assert "gone into business for themselves" in " ".join(report.play_by_play)
    assert f"{w2.name} is the winner" in " ".join(report.play_by_play)

def test_morale_work_rate_modifier(roster):
    w1_id, w1, w2_id, w2, _, roster_dict = roster
    
    m1_id = uuid4()
    move = Move(name="Slam", selling_burden=10, stamina_cost=5, heat_generation=20, move_type=MoveType.GRAPPLE)
    moves = {m1_id: move}
    w1.moveset = {m1_id}
    w2.moveset = {m1_id}
    
    booking = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[w1_id], [w2_id]],
        scripting_style=ScriptingStyle.STRICT,
        designated_winner=w1_id,
        expected_runsheet=Runsheet(spots=[m1_id, m1_id, m1_id])
    )
    
    # Full morale match
    w1.morale = 100
    w2.morale = 100
    report_high = simulate_match(booking, roster_dict, moves)
    
    # Tanked morale match
    w1.morale = 20
    w2.morale = 20
    report_low = simulate_match(booking, roster_dict, moves)
    
    # Low morale should produce lower star rating
    assert report_low.star_rating < report_high.star_rating
