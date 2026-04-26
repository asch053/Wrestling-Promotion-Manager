# Storylines & Long-Term Booking - Executive Summary

A wrestling promotion isn't just a series of random athletic contests; it's a soap opera. The Storyline Engine introduces persistent narratives that build over time. A hot storyline draws massive money, while a neglected storyline fizzles out and loses the crowd's interest.

## High-Level Requirements (HLR) Document

**Feature ID**: F-007
**Feature Name**: Storyline Engine & Character Turns
**Description**: Implement a `Storyline` model to track ongoing narratives between wrestlers or factions. Storylines have a `planned_outcome` (e.g., Turn Face, Turn Heel, Push New Star, Build Rivalry) and an internal `excitement` metric that grows with high-quality matches. Match Booking will integrate with storylines to boost starting crowd excitement. The engine supports massive "Payoffs" at the conclusion of a story, rewarding the company and wrestlers based on the success of the narrative.

**User Stories**:
- As a Booker, I want to create a `Storyline` involving specific wrestlers, selecting a `planned_outcome` to guide the narrative.
- As a Booker, I want to assign a `storyline_id` to a Match on the `BookingSheet`.
- As a Referee, when simulating a match attached to a storyline, I want the storyline's `excitement` to act as the base starting `crowd_excitement` for the match.
- As a Booker, I want the Star Rating of a storyline match to increase the storyline's total excitement for the future.
- As a Booker, I want to execute a "Payoff" at the end of the storyline, cashing in the built-up excitement to achieve the `planned_outcome` (e.g., executing the Face/Heel turn, permanently boosting a pushed star's hype, or cementing a legendary rivalry).
- As the Money Man, I want hot storylines to drive up the overall `Company.current_excitement` when paid off.

**Functional Requirements**:
- **FR-7.1.0 - The Storyline Model**: Create `Storyline` model containing `id`, `name`, `participants` (List[UUID]), `excitement` (0-100), `is_active` (bool), and `planned_outcome` (Enum).
- **FR-7.2.0 - Storyline Planned Outcomes**: Implement outcome enums: `TURN_FACE`, `TURN_HEEL`, `PUSH_STAR`, `BUILD_RIVALRY`.
- **FR-7.3.0 - Match Simulator Impact**: In `match_simulator.py`, if a `storyline_id` is present, the match's starting `crowd_excitement` is derived from the storyline's excitement rather than the default `50`. Star Ratings dynamically shift the storyline's ongoing excitement.
- **FR-7.4.0 - Storyline Decay**: If a storyline is not featured on an Event, its excitement decays. 
- **FR-7.5.0 - The Payoff Mechanic**: Introduce `execute_payoff()` logic. 
  - Resolves the `planned_outcome`. (e.g., `TURN_HEEL` deletes friendships and sets rivalry to 100 for the target, while changing their kayfabe_status. `PUSH_STAR` applies a massive permanent Hype boost to the winner based on the final excitement).
  - "Cashes in" the final excitement, giving a lump sum boost to the `Company.current_excitement` for future ticket sales.

**Acceptance Criteria**:
- A match attached to an 80-excitement Storyline starts the simulation with a hot crowd (80) rather than a dead crowd (50).
- Concluding a `TURN_HEEL` storyline successfully changes the wrestler's kayfabe_status to Heel and destroys their friendships with Faces.
- A 5-star match in an active storyline raises the storyline's excitement for the next week's show.

## Logic Blueprint

- **Storyline Match Excitement**: `Starting Crowd = Storyline.excitement`
- **Storyline Progression**: `New Storyline Excitement = Old Excitement + ((Star Rating - 3.0) * 5)`. 
- **Payoff Math**: `Company.excitement += (Storyline.excitement / 10)`. Target Wrestler Hype/Pop gets permanent boost based on outcome.

## File Impact List

- `[NEW]` `src/models/promotion/storyline.py`
- `[MODIFY]` `src/models/promotion/booking/booking_sheet.py`
- `[MODIFY]` `src/engine/match_simulator.py`
- `[NEW]` `src/engine/storyline_manager.py`
- `[MODIFY]` `src/models/promotion/company.py`

## Agent Assignments

- **To Road Agent**: Draft the DLR. Define the exact math for Payoffs and the Enum structure for Planned Outcomes. 
- **To The Booker**: *(Future Step)* Build `storyline_manager.py` to handle the Payoff conclusion logic. Update `match_simulator.py`.
- **To The Referee**: *(Future Step)* Write tests proving that Storyline matches start with hot crowds and that Payoffs correctly mutate the wrestlers according to their Planned Outcome.
