# Match Simulation Engine - Executive Summary

The Match Simulation Engine is the beating heart of the Wrestling Promotion Manager. It is responsible for taking a `BookingSheet`, retrieving the involved `Wrestler` and `Move` data, and executing a turn-based simulation to determine how the match unfolds. It calculates the physical toll on the wrestlers, the psychological flow of the match, and ultimately produces a "Match Report" detailing the spots, the crowd reaction (Star Rating), and the final outcome.

## High-Level Requirements (HLR) Document

**Feature ID**: F-003
**Feature Name**: Match Simulation Engine
**Description**: Implement a stateless, turn-based simulation engine that processes a `BookingSheet` and outputs a `MatchReport` detailing the events, stat changes, and final rating of the match.

**User Stories**:
- As a Booker, I want the engine to read my `BookingSheet` and simulate the match so I can see if my booking decisions resulted in a 5-star classic or a dud.
- As the Simulation Engine, I need to process the differences between `STRICT` matches (following the runsheet exactly) and `CALLED_IN_RING` matches (using RNG and wrestler stats to pick spots) to determine the flow.
- As a Fan, I want to see a log of the match (e.g., "Hulk Hogan hits a Leg Drop for 20 damage!") so I can read the play-by-play.

**Functional Requirements**:
- **FR-3.1.0 - Core Engine Loop**: Implement a `simulate_match(booking_sheet: BookingSheet, wrestlers: Dict[UUID, Wrestler], move_library: Dict[UUID, Move]) -> MatchReport` function.
- **FR-3.2.0 - Turn Execution**: The engine must loop through "spots" until the match concludes. For `STRICT`, spots are pulled from the `expected_runsheet`. For `CALLED_IN_RING`, spots are dynamically selected from the executing wrestler's `moveset`.
- **FR-3.3.0 - Damage & Stamina Tracking**: Track the current health and stamina of each wrestler. When a move is executed, deduct the `stamina_cost` from the attacker and apply `damage` to the defender.
- **FR-3.4.0 - Finish Execution**: The engine MUST end the match with the `designated_winner` going over. 
- **FR-3.5.0 - The Match Report**: The engine must output a `MatchReport` object containing a `play_by_play` log (List of strings) and a `star_rating` (float from 0.0 to 5.0).

**Acceptance Criteria**:
- The engine successfully completes a simulation and returns a valid `MatchReport`.
- The `designated_winner` is always the victor in the generated `play_by_play` log.
- The simulation does not mutate the original `Wrestler` objects (stateless simulation; a temporary state object must be used during the match).

## Logic Blueprint

- **Stateless Execution**: The engine should instantiate a temporary `MatchState` object to track current health, stamina, and momentum for the duration of the match. The base `Wrestler` stats remain unchanged.
- **Star Rating Math**: 
  - Base rating starts at 2.0.
  - Add points based on the average `work_rate` of the participants.
  - Add points for `heat_generation` of the moves executed.
  - Subtract points if a wrestler's `stamina` drops below 0 (simulating botches/sloppiness).
- **The "Screwjob" Check (Future Proofing)**: If the `designated_winner` has terrible `professionalism` and high `ego`, we might want to flag a "botched finish" in future updates, but for now, enforce the booked finish strictly.

## File Impact List

- `[NEW]` `src/engine/match_simulator.py`
- `[NEW]` `src/engine/models/match_state.py`
- `[NEW]` `src/engine/models/match_report.py`

## Agent Assignments

- **To Road Agent**: Draft the DLR. Define the `MatchReport` and `MatchState` Pydantic models. Design the step-by-step logic loop for `simulate_match` so The Booker knows exactly how to calculate damage and select moves. Define tests to ensure the designated winner always wins.
- **To The Booker**: *(Future Step)* You will write the heavy math in `src/engine/match_simulator.py`. Be ready to utilize the `InRingSkill` and `Psychology` models you built previously.
- **To The Fan Architect**: *(Future Step)* Prepare an API endpoint that triggers this engine and returns the `MatchReport` JSON.

## Referee Note

**QA Edge Cases to consider in DLR**:
- What happens if a `STRICT` runsheet is exhausted but the finish hasn't happened? Does the engine panic, or does it auto-transition to the finish sequence? (Road Agent needs to define this).
- Verify that base wrestler objects are strictly NOT mutated after a match runs.
