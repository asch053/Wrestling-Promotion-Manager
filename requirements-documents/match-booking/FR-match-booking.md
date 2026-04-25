# Match Booking Sheet - Executive Summary

The Match Booking Sheet provides the structural blueprint for how a match is planned backstage before the wrestlers step into the ring. It dictates the participants, the scripting style (how much freedom the wrestlers have), the predetermined winner, and the sequence of events. This sheet acts as the direct input configuration for the simulation engine to execute the match.

## High-Level Requirements (HLR) Document

**Feature ID**: F-002
**Feature Name**: Match Booking Sheet
**Description**: Create a booking configuration model that defines the parameters of a match, including participants, scripting constraints, the predetermined outcome, and the planned spots/runsheet.

**User Stories**:
- As a Booker, I need to define who is in the match and what type of match it is so the simulation engine knows the rules.
- As a Booker, I want to decide if a match is strictly scripted, allows audibles, or is called in the ring, because this will impact the match quality based on the wrestlers' Psychology and Backstage stats.
- As a Booker, I need to decree "who goes over" (the winner) so the match engine ends the simulation with the correct outcome.
- As the Simulation Engine, I need the Booking Sheet to act as the exact parameters and constraints for the math execution.

**Functional Requirements**:
- **FR-2.1.0 - Core Match Info**: The booking sheet must store `match_type` (e.g., 1v1, Tag, Triple Threat) and the lists of `participants` (Wrestler UUIDs).
- **FR-2.2.0 - Scripting Style**: Must define `scripting_style` as an Enum (`STRICT`, `AUDIBLE`, `CALLED_IN_RING`).
- **FR-2.3.0 - Runsheet Definition**: If `scripting_style` is `STRICT` or `AUDIBLE`, the sheet must allow assigning an `expected_runsheet` (a list of planned spots or move references). If `CALLED_IN_RING`, this field should be empty or ignored by the engine.
- **FR-2.4.0 - Finish Directives**: Must specify `designated_winner` (Wrestler UUID) and any specific finish instructions (e.g., clean pin, interference).

**Acceptance Criteria**:
- A Booking Sheet can be created with `scripting_style=CALLED_IN_RING` without providing an expected runsheet.
- A Booking Sheet created with `scripting_style=STRICT` should ideally validate that an expected runsheet is provided.
- The Booking Sheet correctly links to the Wrestler IDs defined in F-001.
- The `designated_winner` must be validated to be one of the `participants` assigned to the match.

## Logic Blueprint

- **Psychology vs. Scripting**: 
  - `STRICT`: Wrestlers follow the `expected_runsheet`. Match quality depends entirely on their `Work Rate` and the quality of the written runsheet. High `Ego` wrestlers might botch or get frustrated if forced into strict scripts.
  - `AUDIBLE`: Wrestlers follow the runsheet but can deviate if the "heat" drops. Requires high `Work Rate` and `Professionalism` to execute smoothly.
  - `CALLED_IN_RING`: No runsheet. Wrestlers use their own `moveset` dynamically. Match quality relies heavily on `Work Rate`, `Selling`, and `Stamina` to maintain the flow.
- **The Finish**: The engine must force the simulation to end in favor of the `designated_winner`. If a wrestler has high `Ego` and low `Professionalism`, there is a chance they "shoot" and refuse to follow the finish (a Screwjob scenario).

## File Impact List

- `[NEW]` `src/models/promotion/booking/booking_sheet.py`
- `[NEW]` `src/models/promotion/booking/runsheet.py`

## Agent Assignments

- **To Road Agent**: Draft the DLR. Define the Pydantic models for the `BookingSheet` and the Enums for `ScriptingStyle` and `MatchType`. Clearly define the validation logic (e.g., using Pydantic's `@model_validator` to enforce that the `designated_winner` is in the `participants` list, and enforcing runsheet rules based on the scripting style).
- **To The Booker**: *(Future Step)* Prepare to intake this `BookingSheet` object as the single source of truth for the match simulation loop.
- **To The Money Man**: *(Future Step)* Map the Booking Sheet to database tables (e.g., an `events` table and a `matches` table).

## Referee Note

**QA Edge Cases to consider in DLR**:
- Test Pydantic validation: Ensure that if `scripting_style` is `STRICT`, passing a `None` or empty `expected_runsheet` throws a `ValidationError`.
- Verify that setting the `designated_winner` to a UUID that is NOT in the `participants` list throws a `ValidationError`.
