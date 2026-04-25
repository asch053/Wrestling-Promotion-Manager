import pytest
from pydantic import ValidationError
from uuid import uuid4
from src.models.wrestler.moveset import Move, MoveType
from src.models.wrestler.wrestler import Wrestler, Alignment, InRingSkill, Psychology, Backstage, Popularity

def test_create_valid_move():
    move = Move(
        name="Vertical Suplex",
        damage=15,
        stamina_cost=10,
        heat_generation=5,
        move_type=MoveType.GRAPPLE
    )
    assert move.name == "Vertical Suplex"
    assert move.damage == 15
    assert move.move_type == MoveType.GRAPPLE

def test_create_valid_wrestler():
    move_id_1 = uuid4()
    move_id_2 = uuid4()
    
    wrestler = Wrestler(
        name="Hulk Hogan",
        in_ring=InRingSkill(strength=90, agility=40, stamina=80),
        psychology=Psychology(work_rate=70, selling=50),
        backstage=Backstage(ego=100, professionalism=60),
        moveset={move_id_1, move_id_2}
    )
    
    assert wrestler.name == "Hulk Hogan"
    assert wrestler.in_ring.strength == 90
    assert len(wrestler.moveset) == 2

def test_wrestler_stat_out_of_bounds():
    with pytest.raises(ValidationError):
        Wrestler(
            name="Super Man",
            in_ring=InRingSkill(strength=101, agility=40, stamina=80), # Invalid
            psychology=Psychology(work_rate=70, selling=50),
            backstage=Backstage(ego=100, professionalism=60),
            moveset=set()
        )

def test_move_invalid_enum():
    with pytest.raises(ValidationError):
        Move(
            name="Magic Missile",
            damage=15,
            stamina_cost=10,
            heat_generation=5,
            move_type="MAGIC" # Invalid
        )

def test_duplicate_moveset_ids_handled():
    move_id = uuid4()
    
    # Passing a list with duplicates to Pydantic should coerce it to a set of 1
    wrestler = Wrestler(
        name="Repetitive Wrestler",
        in_ring=InRingSkill(strength=50, agility=50, stamina=50),
        psychology=Psychology(work_rate=50, selling=50),
        backstage=Backstage(ego=50, professionalism=50),
        moveset=[move_id, move_id]
    )
    
    assert len(wrestler.moveset) == 1

def test_dynamic_alignment():
    # High Pop, low Heat = FACE
    w = Wrestler(
        name="Face",
        in_ring=InRingSkill(strength=50, agility=50, stamina=50),
        psychology=Psychology(work_rate=50, selling=50),
        backstage=Backstage(ego=50, professionalism=50),
        popularity=Popularity(hype=50, heat=10, pop=80)
    )
    assert w.alignment == Alignment.FACE
    
    # High Heat, low Pop = HEEL
    w.popularity.heat = 90
    w.popularity.pop = 20
    assert w.alignment == Alignment.HEEL
    
    # Close Pop/Heat with high Hype = TWEENER
    w.popularity.hype = 80
    w.popularity.pop = 80
    w.popularity.heat = 70
    assert w.alignment == Alignment.TWEENER

def test_opposing_metric_decay():
    from src.engine.match_simulator import apply_opposing_metric_decay
    
    # Pure babyface: high prof, low ego -> high decay multiplier
    pure_face = Wrestler(
        name="Pure Face",
        in_ring=InRingSkill(strength=50, agility=50, stamina=50),
        psychology=Psychology(work_rate=50, selling=50),
        backstage=Backstage(ego=10, professionalism=90),
        popularity=Popularity(hype=50, heat=50, pop=80)
    )
    
    # Gaining 10 Pop should heavily decay Heat
    pop_d, heat_d = apply_opposing_metric_decay(pure_face, 10, 0)
    assert pop_d == 10
    assert heat_d < 0  # Heat decayed
    
    # Anti-hero: high ego, low prof -> low decay multiplier
    antihero = Wrestler(
        name="Anti-Hero",
        in_ring=InRingSkill(strength=50, agility=50, stamina=50),
        psychology=Psychology(work_rate=50, selling=50),
        backstage=Backstage(ego=90, professionalism=10),
        popularity=Popularity(hype=50, heat=50, pop=50)
    )
    
    pop_d2, heat_d2 = apply_opposing_metric_decay(antihero, 10, 0)
    # Pure face (high prof, low ego) = high decay = loses MORE heat when gaining Pop
    # Anti-hero (high ego, low prof) = low decay = loses LESS heat (can hold both)
    # So anti-hero's heat_d should be LESS negative (closer to 0) than pure face
    assert heat_d2 > heat_d
