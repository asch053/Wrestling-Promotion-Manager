# Backstage Politics & Locker Room Morale - Detailed Logic Requirements (DLR)

## Traceability Table

| DLR ID | Linked HLR ID | Technical Requirement Explanation | Confirmation Test Case |
| :--- | :--- | :--- | :--- |
| *DLR-8.1.1* | *FR-8.1.0* | Add `morale: int = Field(ge=0, le=100, default=50)` to the `Wrestler` model. Add `wins: int = 0` and `losses: int = 0` counters. | Verify instantiation with default morale of 50. |
| *DLR-8.2.1* | *FR-8.2.0* | Implement `calculate_morale_shift(wrestler, was_booked, won, company, storylines)` in `morale_engine.py`. Returns the total morale delta as an integer. | Verify a wrestler who won gets +5 base shift. |
| *DLR-8.2.2* | *FR-8.2.0* | **Booking Result**: `Won = +5`, `Lost = -3`, `Not Booked = -5`. | Verify benched wrestler loses 5 morale. |
| *DLR-8.2.3* | *FR-8.2.0* | **Ego Amplifier**: If the base shift is negative, multiply it by `(1 + ego / 100)`. A 100-Ego wrestler suffers `2x` the negative shift. A 0-Ego wrestler suffers `1x`. | Verify 100-ego wrestler losing gets `-6` (3 * 2) instead of `-3`. |
| *DLR-8.2.4* | *FR-8.2.0* | **Storyline Boost**: If the wrestler is the `target_wrestler` of any active storyline with `planned_outcome == PUSH_STAR`, add `+10`. | Verify wrestler on a push gets +10 boost. |
| *DLR-8.2.5* | *FR-8.2.0* | **Financial Fairness**: Iterate `company.current_roster`. If any peer has `hype < wrestler.hype` AND `weekly_salary > wrestler.weekly_salary`, apply `-10`. Only triggers once regardless of how many underpaying peers exist. | Verify underpaid wrestler loses 10 morale. Verify fairly paid wrestler is unaffected. |
| *DLR-8.3.1* | *FR-8.3.0* | Implement `generate_incidents(company, roster_dict)` in `incident_generator.py`. Returns a `List[Incident]`. For each wrestler where `ego > 70 AND professionalism < 40 AND morale < 30`, roll `random.random()` against the probability table. | Verify no incidents for a wrestler with 50 ego. |
| *DLR-8.3.2* | *FR-8.3.0* | **Incident Model**: `class Incident(BaseModel)`: `wrestler_id: UUID`, `incident_type: IncidentType`, `description: str`. `class IncidentType(str, Enum)`: `REFUSAL_TO_LOSE`, `LOCKER_ROOM_POISON`, `PUBLIC_SHOOTING`. | Verify Incident instantiation. |
| *DLR-8.3.3* | *FR-8.3.0* | **Probability Table**: Roll `r = random.random()`. If `r < 0.3` → `REFUSAL_TO_LOSE`. Elif `r < 0.7` → `LOCKER_ROOM_POISON`. Else → `PUBLIC_SHOOTING`. | Verify distribution via seeded random. |
| *DLR-8.3.4* | *FR-8.3.0* | **Refusal to Lose**: In `match_simulator.py`, before finalizing the winner, check if any participant has an active `REFUSAL_TO_LOSE` incident. If so, override `designated_winner` to that wrestler's ID. Add narrative: `"{name} has gone into business for themselves!"`. | Verify `MatchReport.designated_winner` is overridden. |
| *DLR-8.3.5* | *FR-8.3.0* | **Locker Room Poison**: Apply `-15` morale to every member of the wrestler's faction (via `faction_id`). If no faction, apply `-5` to 2 random roster members. | Verify faction members lose 15 morale. |
| *DLR-8.3.6* | *FR-8.3.0* | **Public Shooting**: Reduce `company.base_excitement_modifier` by `5`. | Verify company excitement drops. |
| *DLR-8.4.1* | *FR-8.4.0* | In `match_simulator.py`, when calculating `avg_work_rate`, use `effective_work_rate = work_rate * (morale / 100.0)` instead of raw `work_rate`. | Verify a 20-morale wrestler with 80 work_rate produces effective_work_rate of 16. |
| *DLR-8.5.1* | *FR-8.5.0* | Implement `calculate_resign_difficulty(wrestler)` in `morale_engine.py`. Returns a float (0.0 to 1.0). `difficulty = 1.0 - (morale / 100.0)`. A wrestler at 20 morale has 0.8 difficulty (80% chance of refusing or demanding more). | Verify 100 morale = 0.0 difficulty. Verify 0 morale = 1.0 difficulty. |

## Technical Specs & Architecture

- **Affected Files**:
  - `src/models/wrestler/wrestler.py` [MODIFY]
  - `src/engine/match_simulator.py` [MODIFY]
  - `src/engine/morale_engine.py` [NEW]
  - `src/engine/incident_generator.py` [NEW]

- **Data Structures**:
  - `wrestler.py`:
    - Add `morale: int = Field(ge=0, le=100, default=50)`
    - Add `wins: int = 0`
    - Add `losses: int = 0`
  - `incident_generator.py`:
    - `class IncidentType(str, Enum)`
    - `class Incident(BaseModel)`: `wrestler_id`, `incident_type`, `description`

- **Logic Flow**:
  1. **End of Event**: The Booker calls `calculate_morale_shift()` for every roster member, passing whether they were booked and whether they won.
  2. **Post-Morale Calculation**: The Booker calls `generate_incidents(company, roster_dict)`. The engine evaluates every wrestler against the trigger threshold (`ego > 70 AND prof < 40 AND morale < 30`) and rolls for incidents.
  3. **Incident Resolution**:
     - `REFUSAL_TO_LOSE`: Stored as a flag. On the wrestler's **next** match, the simulator checks for active refusal incidents and overrides the winner.
     - `LOCKER_ROOM_POISON`: Applied immediately to faction members.
     - `PUBLIC_SHOOTING`: Applied immediately to company excitement.
  4. **Match Simulation**: When calculating Star Rating, the simulator uses `effective_work_rate = work_rate * (morale / 100)` for each participant.

## Work Order Refinement

- **To The Booker**:
  - **WARNING**: The `REFUSAL_TO_LOSE` mechanic modifies the `designated_winner` in the `MatchReport`. This means the `MatchReport` output may differ from the `BookingSheet` input. Downstream systems (e.g., storyline progression, morale shifts) must use the **report's** winner, not the booking's.
  - The morale modifier on Work Rate must be applied **before** `calculate_star_rating()` is called.
- **To The Money Man**:
  - The `calculate_resign_difficulty()` function is a placeholder for a future Contract Negotiation system. For now, just implement the formula and expose it.

## Referee Handbook (QA Scenarios)

- **Morale Shift Tests**:
  - `test_morale_win_boost`: Wrestler wins. Assert morale increased by 5.
  - `test_morale_loss_ego_amplifier`: 100-Ego wrestler loses. Assert morale dropped by 6 (3 * 2.0).
  - `test_morale_benched_decay`: Wrestler not booked. Assert morale dropped by 5.
  - `test_morale_push_storyline_boost`: Wrestler is target of PUSH_STAR. Assert +10 boost.
  - `test_morale_financial_fairness`: Wrestler is underpaid vs lower-hype peer. Assert -10 penalty.
- **Incident Tests**:
  - `test_incident_trigger_threshold`: Wrestler with ego=80, prof=20, morale=20 triggers an incident. Wrestler with ego=50 does NOT trigger.
  - `test_refusal_to_lose`: Simulate a match where a participant has a REFUSAL_TO_LOSE incident. Assert the `MatchReport` winner differs from the `BookingSheet` winner.
  - `test_locker_room_poison`: Assert all faction members lose 15 morale.
  - `test_public_shooting`: Assert company excitement modifier drops by 5.
- **In-Ring Tests**:
  - `test_morale_work_rate_modifier`: Two identical matches. One with 100 morale wrestlers, one with 20 morale. Assert the low-morale match produces a significantly lower Star Rating.
