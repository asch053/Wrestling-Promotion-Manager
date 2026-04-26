import pytest
from uuid import uuid4
from src.models.wrestler.wrestler import Wrestler, InRingSkill, Psychology, Backstage, KayfabeStatus, Popularity
from src.models.wrestler.moveset import Move, MoveType
from src.models.promotion.booking.booking_sheet import BookingSheet, ScriptingStyle, MatchType
from src.models.promotion.booking.runsheet import Runsheet
from src.engine.match_simulator import simulate_match, calculate_star_rating

@pytest.fixture
def base_data():
    w1_id = uuid4()
    w2_id = uuid4()
    w3_id = uuid4()
    w4_id = uuid4()
    m1_id = uuid4()
    m2_id = uuid4()
    
    w1 = Wrestler(
        name="Wrestler A",
        in_ring=InRingSkill(strength=80, agility=80, stamina=100),
        psychology=Psychology(work_rate=80, selling=80, intelligence=100),
        backstage=Backstage(ego=50, professionalism=100),
        popularity=Popularity(hype=50, heat=0, pop=80),
        moveset={m1_id}
    )
    
    w2 = Wrestler(
        name="Wrestler B",
        in_ring=InRingSkill(strength=70, agility=70, stamina=100),
        psychology=Psychology(work_rate=10, selling=10, intelligence=0),
        backstage=Backstage(ego=50, professionalism=0),
        popularity=Popularity(hype=50, heat=80, pop=0),
        moveset={m2_id}
    )
    
    w3 = Wrestler(
        name="Wrestler C",
        in_ring=InRingSkill(strength=80, agility=80, stamina=100),
        psychology=Psychology(work_rate=80, selling=80, intelligence=100),
        backstage=Backstage(ego=50, professionalism=100),
        popularity=Popularity(hype=50, heat=0, pop=80),
        moveset={m1_id}
    )
    
    w4 = Wrestler(
        name="Wrestler D",
        in_ring=InRingSkill(strength=70, agility=70, stamina=100),
        psychology=Psychology(work_rate=10, selling=10, intelligence=0),
        backstage=Backstage(ego=50, professionalism=0),
        popularity=Popularity(hype=50, heat=80, pop=0),
        moveset={m2_id}
    )
    
    move1 = Move(name="Slam", selling_burden=10, stamina_cost=5, heat_generation=20, move_type=MoveType.GRAPPLE)
    move2 = Move(name="Kick", selling_burden=5, stamina_cost=2, heat_generation=5, move_type=MoveType.STRIKE)
    
    return {
        "w1_id": w1_id,
        "w2_id": w2_id,
        "w3_id": w3_id,
        "w4_id": w4_id,
        "m1_id": m1_id,
        "m2_id": m2_id,
        "wrestlers": {w1_id: w1, w2_id: w2, w3_id: w3, w4_id: w4},
        "moves": {m1_id: move1, m2_id: move2}
    }

def test_simulate_strict_match(base_data):
    w1_id = base_data["w1_id"]
    w2_id = base_data["w2_id"]
    m1_id = base_data["m1_id"]
    
    booking = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[w1_id], [w2_id]],
        scripting_style=ScriptingStyle.STRICT,
        designated_winner=w1_id,
        expected_runsheet=Runsheet(spots=[m1_id, m1_id, m1_id])
    )
    
    report = simulate_match(booking, base_data["wrestlers"], base_data["moves"])
    
    assert len(report.play_by_play) == 4 # 3 spots + finish
    assert "Wrestler A" in report.play_by_play[-1]
    assert "winner" in report.play_by_play[-1].lower()
    assert report.final_crowd_excitement != 50
    assert w1_id in report.wrestler_deltas

def test_simulate_called_in_ring_match(base_data):
    w1_id = base_data["w1_id"]
    w2_id = base_data["w2_id"]
    
    booking = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[w1_id], [w2_id]],
        scripting_style=ScriptingStyle.CALLED_IN_RING,
        designated_winner=w2_id
    )
    
    report = simulate_match(booking, base_data["wrestlers"], base_data["moves"])
    
    assert len(report.play_by_play) >= 6

def test_professionalism_mitigation(base_data):
    w1_id = base_data["w1_id"]
    w2_id = base_data["w2_id"]
    m2_id = base_data["m2_id"]
    
    base_data["wrestlers"][w1_id].psychology.work_rate = 0
    base_data["wrestlers"][w2_id].psychology.work_rate = 0
    
    booking = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[w1_id], [w2_id]],
        scripting_style=ScriptingStyle.STRICT,
        designated_winner=w1_id,
        expected_runsheet=Runsheet(spots=[m2_id])
    )
    
    report = simulate_match(booking, base_data["wrestlers"], base_data["moves"])
    
    assert report.star_rating < 2.5
    delta1 = report.wrestler_deltas[w1_id]
    delta2 = report.wrestler_deltas[w2_id]
    
    # W1 has high professionalism -> mitigation -> hype delta should be 0
    assert delta1.hype_delta == 0
    # W2 has low professionalism -> no mitigation -> negative hype
    assert delta2.hype_delta < 0

def test_crowd_reading_audible(base_data):
    w1_id = base_data["w1_id"]
    w2_id = base_data["w2_id"]
    m1_id = base_data["m1_id"]
    m2_id = base_data["m2_id"]
    
    base_data["wrestlers"][w1_id].moveset = {m1_id, m2_id}
    
    booking = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[w1_id], [w2_id]],
        scripting_style=ScriptingStyle.CALLED_IN_RING,
        designated_winner=w1_id
    )
    report = simulate_match(booking, base_data["wrestlers"], base_data["moves"])
    assert report.final_crowd_excitement is not None
def test_storyline_starting_heat(base_data):
    w1_id = base_data["w1_id"]
    w2_id = base_data["w2_id"]
    
    from src.models.promotion.storyline import Storyline, PlannedOutcome
    s_id = uuid4()
    s = Storyline(
        id=s_id,
        name="Hot Feud",
        planned_outcome=PlannedOutcome.BUILD_RIVALRY,
        excitement=90
    )
    storylines = {s_id: s}
    
    booking = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[w1_id], [w2_id]],
        scripting_style=ScriptingStyle.CALLED_IN_RING,
        designated_winner=w1_id,
        storyline_id=s_id
    )
    
    report = simulate_match(booking, base_data["wrestlers"], base_data["moves"], storylines)
    
    # The starting heat was 90. If the match isn't long, it should end > 50.
    assert report.final_crowd_excitement > 70
    assert report.storyline_id == s_id
    assert report.storyline_delta != 0
def test_tag_team_simulation(base_data):
    w1_id = base_data["w1_id"]
    w2_id = base_data["w2_id"]
    w3_id = base_data["w3_id"]
    w4_id = base_data["w4_id"]
    
    booking = BookingSheet(
        match_type=MatchType.TWO_ON_TWO,
        teams=[[w1_id, w3_id], [w2_id, w4_id]],
        scripting_style=ScriptingStyle.CALLED_IN_RING,
        designated_winner=w1_id
    )
    
    report = simulate_match(booking, base_data["wrestlers"], base_data["moves"])
    assert len(report.wrestler_deltas) == 4

def test_rivalry_heat_boost(base_data):
    w1_id = base_data["w1_id"]
    w2_id = base_data["w2_id"]
    m1_id = base_data["m1_id"]
    
    booking_normal = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[w1_id], [w2_id]],
        scripting_style=ScriptingStyle.STRICT,
        designated_winner=w1_id,
        expected_runsheet=Runsheet(spots=[m1_id, m1_id, m1_id])
    )
    
    report_normal = simulate_match(booking_normal, base_data["wrestlers"], base_data["moves"])
    
    # Now set them as rivals
    base_data["wrestlers"][w1_id].rivalries[w2_id] = 100
    
    report_rival = simulate_match(booking_normal, base_data["wrestlers"], base_data["moves"])
    
    assert report_rival.star_rating > report_normal.star_rating
