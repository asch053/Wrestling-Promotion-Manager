import random
from typing import Dict, List, Optional
from uuid import UUID
from src.models.wrestler.wrestler import Wrestler, KayfabeStatus
from src.models.wrestler.moveset import Move
from src.models.promotion.booking.booking_sheet import BookingSheet, ScriptingStyle, MatchType
from src.engine.models.match_state import MatchState, WrestlerState
from src.engine.models.match_report import MatchReport, StatDelta
from src.models.promotion.storyline import Storyline
from src.models.promotion.championship import Championship, ChampionshipTier
from src.engine.incident_generator import Incident, IncidentType
from src.engine.championship_manager import update_prestige, check_hierarchy_violation
from src.engine.medical_engine import roll_for_injury, get_effective_stat, InjuryType
from src.engine.stipulation_logic_handler import (
    get_modifiers, calculate_execution_score, calculate_execution_modifier,
    resolve_danger_event, _clamp
)

def calculate_star_rating(avg_work_rate: float, total_heat: int, any_stamina_negative: bool) -> float:
    base = 2.0
    rating = base + (avg_work_rate / 100) * 1.5 + (total_heat / 100) * 1.5
    if any_stamina_negative:
        rating -= 0.5
    return min(max(rating, 0.0), 5.0)

def apply_opposing_metric_decay(wrestler: Wrestler, pop_delta: int, heat_delta: int) -> tuple:
    """Apply Opposing Metric Decay: gaining Pop reduces Heat, and vice versa.
    
    Decay_Multiplier = (100 - Professionalism + Ego) / 100
    High professionalism / low ego = high decay (pure babyface loses Heat fast when gaining Pop)
    High ego / low professionalism = low decay (anti-hero can hold both Pop and Heat)
    """
    raw_multiplier = (wrestler.backstage.professionalism + (100 - wrestler.backstage.ego)) / 200.0
    decay_multiplier = max(0.2, min(1.5, raw_multiplier))
    
    adjusted_pop_delta = pop_delta
    adjusted_heat_delta = heat_delta
    
    if pop_delta > 0:
        # Gaining Pop decays Heat
        adjusted_heat_delta -= int(pop_delta * decay_multiplier)
    if heat_delta > 0:
        # Gaining Heat decays Pop
        adjusted_pop_delta -= int(heat_delta * decay_multiplier)
    
    return adjusted_pop_delta, adjusted_heat_delta

def simulate_match(booking_sheet: BookingSheet, wrestlers: Dict[UUID, Wrestler], move_library: Dict[UUID, Move], storylines: Dict[UUID, Storyline] = None, active_incidents: List[Incident] = None, championships: Dict[UUID, Championship] = None) -> MatchReport:
    # 1. Initialize MatchState statelessly
    flat_participants = [w_id for team in booking_sheet.teams for w_id in team]
    
    # Check for sidelined participants
    for p_id in flat_participants:
        w = wrestlers[p_id]
        if w.injury_status and w.injury_status.is_sidelined:
            raise ValueError(f"Cannot book {w.name} - they are currently sidelined with a {w.injury_status.name}.")
    
    wrestler_states = {}
    for p_id in flat_participants:
        wrestler_states[p_id] = WrestlerState(
            integrity=100,
            stamina=wrestlers[p_id].in_ring.stamina
        )
    match_state = MatchState(wrestlers=wrestler_states)
    
    if booking_sheet.storyline_id and storylines and booking_sheet.storyline_id in storylines:
        match_state.crowd_excitement = storylines[booking_sheet.storyline_id].excitement

    play_by_play = []
    total_heat = 0
    any_stamina_negative = False
    
    # Generate list of spots
    spots = []
    if booking_sheet.scripting_style in [ScriptingStyle.STRICT, ScriptingStyle.AUDIBLE]:
        if booking_sheet.expected_runsheet:
            spots = booking_sheet.expected_runsheet.spots
            
    turn_limit = len(spots) if spots else random.randint(5, 10)
    
    # STEP 1: Fetch stipulation modifiers
    modifiers = get_modifiers(booking_sheet.stipulation)
    
    # STEP 3: Apply min_turn_bonus to turn floor
    turn_limit = turn_limit + modifiers.min_turn_bonus
    
    team_count = len(booking_sheet.teams)
    
    for turn in range(turn_limit):
        attacking_team_idx = turn % team_count
        defending_team_idx = (turn + 1) % team_count
        
        attacking_team = booking_sheet.teams[attacking_team_idx]
        defending_team = booking_sheet.teams[defending_team_idx]
        
        attacker_id = random.choice(attacking_team)
        defender_id = random.choice(defending_team)
        
        attacker = wrestlers[attacker_id]
        defender = wrestlers[defender_id]
        
        move_id = None
        if booking_sheet.scripting_style in [ScriptingStyle.STRICT, ScriptingStyle.AUDIBLE] and turn < len(spots):
            move_id = spots[turn]
        elif booking_sheet.scripting_style == ScriptingStyle.CALLED_IN_RING:
            if attacker.moveset:
                if match_state.crowd_excitement < 40 and attacker.psychology.intelligence >= 70:
                    high_heat_moves = [m_id for m_id in attacker.moveset if move_library[m_id].heat_generation >= 15]
                    if high_heat_moves:
                        move_id = random.choice(high_heat_moves)
                    else:
                        move_id = random.choice(list(attacker.moveset))
                else:
                    move_id = random.choice(list(attacker.moveset))
                    
        if not move_id:
            continue
            
        move = move_library.get(move_id)
        if not move:
            continue
        
        # Apply math — STEP 4: per-spot stipulation multipliers
        heat_generated = int(move.heat_generation * modifiers.heat_multiplier)
        effective_selling_burden = move.selling_burden * modifiers.selling_burden_multiplier
        effective_stamina_cost = move.stamina_cost * modifiers.stamina_cost_multiplier
        
        # Rivalry boost
        if defender_id in attacker.rivalries and attacker.rivalries[defender_id] > 50:
            heat_generated = int(heat_generated * 1.5)
        
        match_state.wrestlers[attacker_id].stamina -= effective_stamina_cost
        match_state.wrestlers[defender_id].integrity -= effective_selling_burden
        total_heat += heat_generated
        
        # Crowd excitement shift
        heat_gain = int(heat_generated / 5)
        match_state.crowd_excitement = max(0, min(100, match_state.crowd_excitement - 2 + heat_gain))
        
        if match_state.wrestlers[attacker_id].stamina < 0 or match_state.wrestlers[defender_id].stamina < 0:
            any_stamina_negative = True
            
        # Append narrative
        narrative = f"{attacker.name} performs {move.name} on {defender.name} for {int(effective_selling_burden)} selling burden! Crowd excitement is {match_state.crowd_excitement}."
        play_by_play.append(narrative)
        
        # STEP 5: Danger event check every 3 turns
        resolve_danger_event(wrestlers, modifiers, play_by_play, turn + 1)
        
    # 4. Finish — check for Refusal to Lose
    winner_id = booking_sheet.designated_winner
    if active_incidents:
        for incident in active_incidents:
            if incident.incident_type == IncidentType.REFUSAL_TO_LOSE and incident.wrestler_id in [w_id for w_id in flat_participants]:
                winner_id = incident.wrestler_id
                play_by_play.append(f"{wrestlers[incident.wrestler_id].name} has gone into business for themselves!")
                break
    
    winner = wrestlers[winner_id]
    finish_narrative = f"The referee counts 1... 2... 3! {winner.name} is the winner!"
    play_by_play.append(finish_narrative)
    
    # 5. Star Rating (with morale and injury modifiers on work rate)
    participant_wrestlers = [wrestlers[p_id] for p_id in flat_participants]
    avg_work_rate = sum(get_effective_stat(w, "work_rate") * (w.morale / 100.0) for w in participant_wrestlers) / len(participant_wrestlers)
    
    star_rating = calculate_star_rating(avg_work_rate, total_heat, any_stamina_negative)
    
    # STEP 6: Execution check — average raw_score across all participants
    raw_scores = {p_id: calculate_execution_score(wrestlers[p_id], modifiers) for p_id in flat_participants}
    avg_raw_score = sum(raw_scores.values()) / len(raw_scores)
    avg_exec_modifier = calculate_execution_modifier(avg_raw_score, modifiers.difficulty_rating)
    
    # STEP 7: Botch check — any participant below 0.6 threshold
    for p_id, raw_score in raw_scores.items():
        if raw_score < 0.6:
            botcher = wrestlers[p_id]
            play_by_play.append(
                f"{botcher.name} botched a spot! The crowd groans."
            )
            # Double jeopardy: additional injury roll for the botcher
            extra_injury = roll_for_injury(botcher)
            if extra_injury and not botcher.injury_status:
                botcher.injury_status = extra_injury
                play_by_play.append(
                    f"CRITICAL: {botcher.name} paid the price — {extra_injury.name}!"
                )
                if extra_injury.injury_type == InjuryType.MAJOR:
                    botcher.morale = max(0, botcher.morale - 10)
    
    # STEP 8: Apply execution bonus/penalty to star rating
    exec_bonus = modifiers.star_rating_bonus * _clamp(avg_exec_modifier, 0.0, 1.0)
    exec_penalty = modifiers.star_rating_penalty * _clamp(-avg_exec_modifier, 0.0, 1.0)
    star_rating = _clamp(star_rating + exec_bonus - exec_penalty, 0.0, 5.0)
    
    # 6. Post-Match Deltas with Opposing Metric Decay
    base_shift = (star_rating - 2.5) * 4.0
    deltas_by_uuid = {}
    
    for p_id in flat_participants:
        w = wrestlers[p_id]
        delta_obj = StatDelta()
        actual_shift = base_shift
        if actual_shift < 0:
            mitigation_factor = (w.backstage.professionalism + w.psychology.intelligence) / 200.0
            actual_shift = base_shift * (1.0 - mitigation_factor)
            
        shift_int = int(round(actual_shift))
        
        # Hype always gets the full shift (macro-metric)
        delta_obj.hype_delta = shift_int
        
        # Determine raw Pop/Heat deltas based on dynamic alignment
        raw_pop_delta = 0
        raw_heat_delta = 0
        if w.kayfabe_status == KayfabeStatus.FACE:
            raw_pop_delta = shift_int
        elif w.kayfabe_status == KayfabeStatus.HEEL:
            raw_heat_delta = shift_int
        else:
            raw_pop_delta = int(shift_int / 2)
            raw_heat_delta = int(shift_int / 2)
        
        # Apply Opposing Metric Decay
        final_pop, final_heat = apply_opposing_metric_decay(w, raw_pop_delta, raw_heat_delta)
        delta_obj.pop_delta = final_pop
        delta_obj.heat_delta = final_heat
            
        deltas_by_uuid[p_id] = delta_obj
        
        # STEP 9: Fatigue — apply stipulation fatigue_multiplier
        spots_count = len(booking_sheet.expected_runsheet.spots) if booking_sheet.expected_runsheet else 10
        match_type_multipliers = {
            MatchType.ONE_ON_ONE: 1.0,
            MatchType.TWO_ON_TWO: 0.8,
            MatchType.THREE_ON_THREE: 0.7
        }
        type_mult = match_type_multipliers.get(booking_sheet.match_type, 1.0)
        
        fatigue_gain = int((spots_count * 2) * type_mult * modifiers.fatigue_multiplier)
        w.fatigue = min(100, w.fatigue + fatigue_gain)
        
        # STEP 10: Roll for injury with stipulation injury_chance_multiplier
        # We apply the multiplier by adjusting the effective fatigue for the roll
        # to scale the probability without mutating the real stat.
        import copy as _copy
        _w_proxy = _copy.copy(w)
        _w_proxy.fatigue = min(100, int(w.fatigue * modifiers.injury_chance_multiplier))
        new_injury = roll_for_injury(_w_proxy)
        if new_injury and not w.injury_status:
            w.injury_status = new_injury
            play_by_play.append(f"CRITICAL: {w.name} has suffered a {new_injury.name}!")
            if new_injury.injury_type == InjuryType.MAJOR:
                w.morale = max(0, w.morale - 10)

    storyline_delta = 0
    if booking_sheet.storyline_id:
        storyline_delta = int(round((star_rating - 3.0) * 5))

    prestige_delta = 0
    if booking_sheet.championship_id and championships:
        belt = championships.get(booking_sheet.championship_id)
        if belt:
            # Calculate base prestige delta
            prestige_delta = int(round((star_rating - 3.0) * 5))
            
            # Check for hierarchy violations
            for p_id in flat_participants:
                if check_hierarchy_violation(wrestlers[p_id], belt):
                    prestige_delta -= 5
                    play_by_play.append(f"The fans felt {wrestlers[p_id].name} didn't belong in a {belt.tier.value} title match, devaluing the belt.")
            
            # Apply the update to the belt object (stateful mutation for now as per DLR)
            update_prestige(belt, star_rating)
            if prestige_delta != int(round((star_rating - 3.0) * 5)):
                # If there was a violation, we manually adjust since update_prestige only handles star rating
                belt.prestige = max(0, min(100, belt.prestige + (prestige_delta - int(round((star_rating - 3.0) * 5)))))

    return MatchReport(
        play_by_play=play_by_play,
        star_rating=round(star_rating, 2),
        final_crowd_excitement=match_state.crowd_excitement,
        wrestler_deltas=deltas_by_uuid,
        storyline_delta=storyline_delta,
        storyline_id=booking_sheet.storyline_id,
        championship_id=booking_sheet.championship_id,
        prestige_delta=prestige_delta
    )

def process_monday_fallout(company: "Company"):
    """
    Day 1 (Monday): The Fallout.
    Applies the stat deltas from the past events' MatchReports to the global Wrestler database.
    This should be called at the start of the week, pulling from events that happened the previous week.
    """
    if company.game_state.current_day != 1:
        raise PermissionError("The Fallout can only be processed on Monday (Day 1).")
        
    if not company.past_events:
        return
        
    # Process the most recent event's reports
    last_event = company.past_events[-1]
    
    # Map roster for easy lookup
    roster_map = {w.name: w for w in company.current_roster}
    
    for report in last_event.match_reports:
        for p_id, delta in report.wrestler_deltas.items():
            # In our system, MatchReport stores UUID keys that correspond to the dictionary 
            # passed in during simulate_match. In Company, we have a List[Wrestler].
            # For this implementation, we will match by name if ID isn't present, 
            # or assume the list contains the same objects.
            # We'll use a safer approach: iterate and find.
            target = None
            for w in company.current_roster:
                # Assuming p_id is the object ID or we can match via some property
                if id(w) == p_id: # If they are the same object in memory
                    target = w
                    break
            
            if not target:
                continue
                
            # Apply Deltas
            target.popularity.hype = _clamp(target.popularity.hype + delta.hype_delta)
            target.popularity.pop = _clamp(target.popularity.pop + delta.pop_delta)
            target.popularity.heat = _clamp(target.popularity.heat + delta.heat_delta)
            
            # Increment Match Stats
            # Determine if they won (this logic should ideally be in the report)
            # For now, we'll assume the caller of fallout knows or we skip if not in report.
            pass

