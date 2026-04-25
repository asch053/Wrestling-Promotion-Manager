# Match Simulation Engine - Detailed Logic Requirements (DLR)

## Traceability Table

| DLR ID | Linked HLR ID | Technical Requirement Explanation | Confirmation Test Case |
| :--- | :--- | :--- | :--- |
| *DLR-3.1.1* | *FR-3.1.0* | Implement `MatchState` & `WrestlerState` Pydantic models. Must contain `health: int` and `stamina: int` (initialized from `Wrestler.in_ring.stamina` and `100` base health). | Verify successful instantiation of MatchState. |
| *DLR-3.1.2* | *FR-3.1.0* | Implement `MatchReport` Pydantic model with `play_by_play: List[str]` and `star_rating: float`. | Verify instantiation of MatchReport. |
| *DLR-3.2.1* | *FR-3.2.0* | `simulate_match` STRICT logic: loop through `expected_runsheet.spots`. Deduct stamina from attacker, apply damage to defender. | Provide a STRICT booking sheet, assert the resulting `play_by_play` length matches the runsheet length + 1 (the finish). |
| *DLR-3.2.2* | *FR-3.2.0* | `simulate_match` CALLED_IN_RING logic: Use `random.choice` on the attacking wrestler's `moveset` to generate 5 to 10 spots dynamically. | Provide CALLED_IN_RING sheet, assert play_by_play length is between 6 and 11. |
| *DLR-3.4.1* | *FR-3.4.0* | Finish logic: The final entry in the `play_by_play` list must explicitly declare the `designated_winner` as the victor. | Assert the last string in `play_by_play` contains the `designated_winner`'s name. |
| *DLR-3.5.1* | *FR-3.5.0* | Star Rating Math: `Base(2.0) + (Avg Work Rate / 100) * 1.5 + (Total Heat / 100) * 1.5`. Max cap at 5.0. Deduct 0.5 if any stamina goes < 0. | Execute match with known stats, assert `star_rating` equals the calculated mathematical expectation. |

## Technical Specs & Architecture

- **Affected Files**:
  - `src/engine/models/match_state.py` [NEW]
  - `src/engine/models/match_report.py` [NEW]
  - `src/engine/match_simulator.py` [NEW]
- **Data Structures**:
  - `match_state.py`:
    - `class WrestlerState(BaseModel)`: Tracks `health` and `stamina`.
    - `class MatchState(BaseModel)`: Contains `wrestlers: Dict[UUID, WrestlerState]`.
  - `match_report.py`:
    - `class MatchReport(BaseModel)`: `play_by_play: List[str]`, `star_rating: float`.
- **Logic Flow** (`match_simulator.py`): 
  1. Initialize `MatchState` from base `Wrestler` objects to ensure a stateless run.
  2. Enter turn loop (determine length via Runsheet or RNG if Called In Ring).
  3. For each turn:
     - Determine attacker/defender (simple alternation for MVP).
     - Select move (from runsheet or dynamically via `random`).
     - Apply math: Deduct `Move.stamina_cost` from attacker, deduct `Move.damage` from defender.
     - Append narrative string to `play_by_play`.
     - Add `Move.heat_generation` to total match heat tracker.
  4. End loop. Append Finish spot narrative for the `designated_winner`.
  5. Calculate `star_rating` using the formula.
  6. Return the completed `MatchReport`.

## Work Order Refinement

- **To The Booker**: 
  - Ensure you initialize the `WrestlerState` cleanly so you do NOT mutate the original `Wrestler` instances passed to `simulate_match`. 
  - Use Python's `random` module for `CALLED_IN_RING` move selection and turn alternation.
- **To The Money Man**: 
  - No database schema changes needed for this specific sprint, but be prepared to store `MatchReport` JSON blobs in the `matches` table later.

## Referee Handbook (QA Scenarios)

- **Positive Tests**:
  - `test_simulate_strict_match`: Pass a STRICT booking sheet. Assert `play_by_play` correctly logs the sequence of moves.
  - `test_simulate_called_in_ring_match`: Pass a CALLED_IN_RING booking sheet. Assert dynamic spots are generated.
  - `test_designated_winner_always_wins`: Assert the last log entry confirms the finish for the designated winner.
- **Math & Edge Case Tests**:
  - `test_star_rating_calculation`: Use stubbed wrestlers with exact known stats to verify the rating formula doesn't break boundaries.
  - `test_stateless_execution`: Assert that the original `Wrestler` object's `stamina` remains entirely unchanged after `simulate_match` completes.
