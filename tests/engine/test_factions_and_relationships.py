import pytest
from uuid import uuid4
from src.models.wrestler.wrestler import Wrestler, Alignment, InRingSkill, Psychology, Backstage, Popularity
from src.models.wrestler.faction import Faction
from src.engine.relationship_engine import calculate_chemistry, apply_relationship
from src.engine.faction_manager import get_bloat_penalty, can_join_faction

@pytest.fixture
def wrestlers():
    w_id1 = uuid4()
    w_id2 = uuid4()
    w_id3 = uuid4()
    
    # Face Guy: high Pop, low Heat -> dynamically FACE
    w1 = Wrestler(
        name="Face Guy",
        in_ring=InRingSkill(strength=50, agility=50, stamina=50),
        psychology=Psychology(work_rate=80, selling=80),
        backstage=Backstage(ego=20, professionalism=80),
        popularity=Popularity(hype=90, heat=0, pop=90)
    )
    
    # Heel Guy: high Heat, low Pop -> dynamically HEEL
    w2 = Wrestler(
        name="Heel Guy",
        in_ring=InRingSkill(strength=50, agility=50, stamina=50),
        psychology=Psychology(work_rate=80, selling=80),
        backstage=Backstage(ego=100, professionalism=80),
        popularity=Popularity(hype=50, heat=90, pop=10)
    )
    
    # Face Buddy: high Pop, low Heat -> dynamically FACE
    w3 = Wrestler(
        name="Face Buddy",
        in_ring=InRingSkill(strength=50, agility=50, stamina=50),
        psychology=Psychology(work_rate=80, selling=80),
        backstage=Backstage(ego=30, professionalism=75),
        popularity=Popularity(hype=90, heat=0, pop=90)
    )
    
    roster_dict = {w_id1: w1, w_id2: w2, w_id3: w3}
    return w_id1, w1, w_id2, w2, w_id3, w3, roster_dict

def test_relationship_chemistry(wrestlers):
    w_id1, w1, w_id2, w2, w_id3, w3, _ = wrestlers
    
    # Face vs Face (w1 vs w3)
    assert w1.alignment == Alignment.FACE
    assert w3.alignment == Alignment.FACE
    score = calculate_chemistry(w1, w3)
    assert score > 50
    
    # Face vs Heel (w1 vs w2)
    assert w2.alignment == Alignment.HEEL
    score2 = calculate_chemistry(w1, w2)
    assert score2 < 50
    
    apply_relationship(w1, w3, w_id1, w_id3)
    assert w_id3 in w1.friendships
    assert w1.friendships[w_id3] > 50

    apply_relationship(w1, w2, w_id1, w_id2)
    assert w_id2 not in w1.friendships
    if score2 < 0:
        assert w_id2 in w1.rivalries

def test_faction_join(wrestlers):
    w_id1, w1, w_id2, w2, w_id3, w3, roster_dict = wrestlers
    
    faction = Faction(
        id=uuid4(),
        name="The Faces",
        leader_id=w_id1,
        members=[w_id1]
    )
    
    # Heel tries to join Face-dominant faction
    assert can_join_faction(w2, faction, w1, w_id2, roster_dict) is False
    
    # High hype Face tries to join
    assert can_join_faction(w3, faction, w1, w_id3, roster_dict) is True

def test_faction_bloat():
    faction = Faction(
        id=uuid4(),
        name="Bloated",
        leader_id=uuid4(),
        members=[uuid4() for _ in range(6)]
    )
    
    assert get_bloat_penalty(faction) == 20 # 6 - 4 = 2 * 10

def test_tweener_faction_flexibility():
    w_id = uuid4()
    leader_id = uuid4()
    
    # Tweener: high hype, close Pop/Heat
    tweener = Wrestler(
        name="Tweener",
        in_ring=InRingSkill(strength=50, agility=50, stamina=50),
        psychology=Psychology(work_rate=50, selling=50),
        backstage=Backstage(ego=30, professionalism=50),
        popularity=Popularity(hype=90, heat=80, pop=80)
    )
    assert tweener.alignment == Alignment.TWEENER
    
    leader = Wrestler(
        name="Leader",
        in_ring=InRingSkill(strength=50, agility=50, stamina=50),
        psychology=Psychology(work_rate=50, selling=50),
        backstage=Backstage(ego=50, professionalism=50),
        popularity=Popularity(hype=80, heat=90, pop=10)
    )
    
    roster_dict = {leader_id: leader, w_id: tweener}
    
    faction = Faction(
        id=uuid4(),
        name="Heel Faction",
        leader_id=leader_id,
        members=[leader_id]
    )
    
    # Tweener should be able to join a Heel-dominant faction
    assert can_join_faction(tweener, faction, leader, w_id, roster_dict) is True
