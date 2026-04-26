# Core Athlete & Move-set Library - Executive Summary

The Core Athlete & Move-set Library is the foundational data model for the Wrestling Promotion Manager. It defines the 'Talent' (Wrestlers) and the 'Production' tools (Moves) they use in the ring. By normalizing the move library, we ensure scalable data management where moves are defined once and referenced by multiple wrestlers.

## High-Level Requirements (HLR) Document

**Feature ID**: F-001
**Feature Name**: Core Athlete & Move-set Library
**Description**: Implement robust models for Wrestlers and a normalized, reusable library for wrestling moves.

**User Stories**:
- As the simulation engine, I need to read a wrestler's stats (In-Ring, Psychology, Backstage) to determine match outcomes and backstage events.
- As a Booker, I want to assign pre-defined moves from a centralized library to a wrestler so I don't have to redefine what a 'Vertical Suplex' is for every athlete.
- As a Fan/Viewer, I need moves to generate 'Heat' and 'Damage' to calculate the impact of a match.

**Functional Requirements**:
- **FR-1.1.0 - Wrestler Model**: The model must include specific attribute groupings: In-Ring Skill (Strength, Agility, Stamina), Psychology (Work Rate, Selling), and Backstage Personality (Ego, Professionalism).
- **FR-1.2.0 - Move Model**: The model must include attributes for Damage, Stamina Cost, Heat Generation, and Move Type (Strike, Grapple, Submission, Aerial, Finisher).
- **FR-1.3.0 - Normalized Library**: Moves must be stored as independent entities and linked to wrestlers via normalized relationships (e.g., IDs) rather than duplicating data.

**Acceptance Criteria**:
- A Wrestler object can be instantiated with the defined attribute categories.
- A Move object can be instantiated with its required attributes.
- A Wrestler can be assigned multiple Moves by reference.

## Logic Blueprint

- **Stat Interactions**: The 'Stamina Cost' of a move should eventually reduce the 'Stamina' stat of the executing wrestler during a match. 'Damage' should reduce the opponent's stamina/integrity.
- **Psychology Math**: A move's 'Heat Generation' combined with the executor's 'Work Rate' and the opponent's 'Selling' will dictate the crowd reaction (Star Rating).
- **Backstage Engine**: 'Ego' and 'Professionalism' will be used outside the ring to determine compliance with booking decisions (e.g., refusing to lose).

## File Impact List

- `[NEW/MODIFY]` `src/models/wrestler/wrestler.py`
- `[NEW]` `src/models/wrestler/moveset.py`

## Agent Assignments

- **To Road Agent**: Draft the Detailed Logic Requirements (DLR) in `./requirements-documents/wrestler-model/DLR-wrestler-model.md`. Define the Pydantic schemas or Python dataclasses for `Wrestler` and `Move`. Define the Enum for `MoveType`. Provide the Traceability Table and set up the confirmation test cases for the Referees.
- **To The Booker**: *(Future Step)* Prepare to use these stats in the match simulation engine. Consider how a 'Finisher' move type bypasses normal selling_burden calculations.
- **To The Money Man**: *(Future Step)* Determine how these models will map to the SQLite database (e.g., a `Wrestler` table, a `Move` table, and a many-to-many `wrestler_moves` association table).

## Referee Note

**QA Edge Cases to consider in DLR**:
- Verify that a Wrestler's stats are bounded (e.g., 0-100).
- Ensure a wrestler cannot be assigned the exact same move reference twice.
- Test that creating a move with invalid Move Types throws an immediate validation error.
