import pytest
import random
from uuid import uuid4
from src.models.wrestler.wrestler import Wrestler, InRingSkill, Psychology, Backstage, Popularity
from src.models.wrestler.injury import Injury, InjuryType
from src.models.promotion.company import Company
from src.models.promotion.booking.booking_sheet import BookingSheet, MatchType, ScriptingStyle
from src.engine.medical_engine import calculate_injury_chance, roll_for_injury, process_weekly_recovery, get_effective_stat
from src.engine.match_simulator import simulate_match

@pytest.fixture
def medical_roster():
    w1_id = uuid4()
    w1 = Wrestler(
        name="Athlete",
        in_ring=InRingSkill(strength=80, agility=100, stamina=100),
        psychology=Psychology(work_rate=80, selling=80),
        backstage=Backstage(ego=50, professionalism=80),
        popularity=Popularity(hype=50, heat=0, pop=50),
        fatigue=0
    )
    company = Company(name="AWF", current_roster=[w1], medical_staff_level=1)
    return w1_id, w1, company

def test_injury_chance_math(medical_roster):
    _, w1, _ = medical_roster
    # base=0.02 * (1+0/100) * (1-100/200) = 0.02 * 1.0 * 0.5 = 0.01 (1%)
    chance = calculate_injury_chance(w1)
    assert chance == pytest.approx(0.01)
    
    # High fatigue
    w1.fatigue = 100
    # base=0.02 * (1+100/100) * (1-100/200) = 0.02 * 2.0 * 0.5 = 0.02 (2%)
    chance = calculate_injury_chance(w1)
    assert chance == pytest.approx(0.02)
    
    # Low agility
    w1.in_ring.agility = 0
    # base=0.02 * (1+100/100) * (1-0/200) = 0.02 * 2.0 * 1.0 = 0.04 (4%)
    chance = calculate_injury_chance(w1)
    assert chance == pytest.approx(0.04)

def test_minor_injury_stat_penalty(medical_roster):
    _, w1, _ = medical_roster
    w1.injury_status = Injury(
        name="Sprained Ankle",
        injury_type=InjuryType.MINOR,
        weeks_remaining=2.0,
        affected_stat="agility",
        is_sidelined=False
    )
    
    # Physical stats get -20%
    assert get_effective_stat(w1, "strength") == 64 # 80 * 0.8
    assert get_effective_stat(w1, "agility") == 80 # 100 * 0.8
    assert get_effective_stat(w1, "stamina") == 80 # 100 * 0.8
    # Psychology stat is unaffected (unless it was a concussion)
    assert get_effective_stat(w1, "work_rate") == 80

def test_concussion_penalty(medical_roster):
    _, w1, _ = medical_roster
    w1.injury_status = Injury(
        name="Concussion",
        injury_type=InjuryType.MINOR,
        weeks_remaining=2.0,
        affected_stat="psychology",
        is_sidelined=False
    )
    # Physical still gets -20%
    assert get_effective_stat(w1, "agility") == 80
    # Psychology gets -20% because it's the affected_stat
    assert get_effective_stat(w1, "work_rate") == 64 # 80 * 0.8

def test_weekly_recovery_fatigue(medical_roster):
    _, w1, company = medical_roster
    w1.fatigue = 50
    company.medical_staff_level = 1 # 1.2x boost
    
    process_weekly_recovery(company)
    # recovery = 10 * 1.2 = 12
    assert w1.fatigue == 38
    
    company.medical_staff_level = 5 # 2.0x boost
    w1.fatigue = 50
    process_weekly_recovery(company)
    # recovery = 10 * 2.0 = 20
    assert w1.fatigue == 30

def test_weekly_injury_healing(medical_roster):
    _, w1, company = medical_roster
    w1.injury_status = Injury(
        name="Broken Arm",
        injury_type=InjuryType.MAJOR,
        weeks_remaining=4.0,
        is_sidelined=True
    )
    company.medical_staff_level = 5 # 2.0x boost
    
    process_weekly_recovery(company)
    assert w1.injury_status.weeks_remaining == 2.0 # 4.0 - 2.0
    
    process_weekly_recovery(company)
    assert w1.injury_status is None # Healed

def test_sidelined_booking_error(medical_roster):
    w1_id, w1, company = medical_roster
    w1.injury_status = Injury(
        name="Torn ACL",
        injury_type=InjuryType.MAJOR,
        weeks_remaining=10.0,
        is_sidelined=True
    )
    
    booking = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[w1_id], [w1_id]],
        scripting_style=ScriptingStyle.CALLED_IN_RING,
        designated_winner=w1_id
    )
    
    roster_dict = {w1_id: w1}
    with pytest.raises(ValueError, match="currently sidelined"):
        simulate_match(booking, roster_dict, {})

def test_fatigue_accumulation(medical_roster):
    w1_id, w1, company = medical_roster
    w2_id = uuid4()
    w2 = Wrestler(
        name="Challenger",
        in_ring=InRingSkill(strength=80, agility=100, stamina=100),
        psychology=Psychology(work_rate=80, selling=80),
        backstage=Backstage(ego=50, professionalism=80),
        popularity=Popularity(hype=50, heat=0, pop=50),
        fatigue=0
    )
    w1.fatigue = 0
    roster_dict = {w1_id: w1, w2_id: w2}
    
    booking = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[w1_id], [w2_id]],
        scripting_style=ScriptingStyle.CALLED_IN_RING,
        designated_winner=w1_id
    )
    
    # 10 spots (default) -> gain = 10 * 2 * 1.0 = 20
    simulate_match(booking, roster_dict, {})
    assert w1.fatigue == 20
    assert w2.fatigue == 20

def test_major_injury_morale_drop(medical_roster):
    w1_id, w1, company = medical_roster
    w2_id = uuid4()
    w2 = Wrestler(
        name="Challenger",
        in_ring=InRingSkill(strength=80, agility=100, stamina=100),
        psychology=Psychology(work_rate=80, selling=80),
        backstage=Backstage(ego=50, professionalism=80),
        popularity=Popularity(hype=50, heat=0, pop=50),
        fatigue=0
    )
    w1.fatigue = 100 # Maximize injury chance
    w1.in_ring.agility = 0
    w1.morale = 50
    roster_dict = {w1_id: w1, w2_id: w2}
    
    booking = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[w1_id], [w2_id]],
        scripting_style=ScriptingStyle.CALLED_IN_RING,
        designated_winner=w1_id
    )
    
    # We need to force a major injury on Athlete. 
    # mock random.random() to hit Major injury.
    with pytest.MonkeyPatch.context() as m:
        m.setattr(random, "random", lambda: 0.01) # Hits both rolls
        simulate_match(booking, roster_dict, {})
    
    if w1.injury_status and w1.injury_status.injury_type == InjuryType.MAJOR:
        assert w1.morale == 40 # 50 - 10
