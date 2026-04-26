# Core Athlete & Move-set Library - Detailed Logic Requirements (DLR)

## Traceability Table

| DLR ID | Linked HLR ID | Technical Requirement Explanation | Confirmation Test Case |
| :--- | :--- | :--- | :--- |
| *DLR-1.1.1* | *FR-1.1.0* | Implement `Wrestler` Pydantic model with `InRingSkill` (strength, agility, stamina), `Psychology` (work_rate, selling), and `Backstage` (ego, professionalism) nested models. | Verify successful instantiation of a `Wrestler` with all nested attribute groups. |
| *DLR-1.1.2* | *FR-1.1.0* | All integer stats must use Pydantic `Field(ge=0, le=100)` validation to enforce 0-100 bounds. | Instantiate `Wrestler` with `ego=-1` and `stamina=105` and expect `ValidationError`. |
| *DLR-1.2.1* | *FR-1.2.0* | Implement `MoveType` as a Python `Enum` (STRIKE, GRAPPLE, SUBMISSION, AERIAL, FINISHER). | Instantiate move with an invalid type string and expect `ValidationError`. |
| *DLR-1.2.2* | *FR-1.2.0* | Implement `Move` Pydantic model with `selling_burden`, `stamina_cost`, `heat_generation` (all integer `ge=0, le=100`), and `move_type` (MoveType). | Verify successful instantiation of a `Move` with valid stats and Enum type. |
| *DLR-1.3.1* | *FR-1.3.0* | The `Wrestler` model should contain a `moveset` attribute which is a `Set[UUID]` or `Set[str]` to store unique Move IDs and prevent duplication. | Assign the same Move ID twice to a wrestler's moveset and verify it is deduplicated. |

## Technical Specs & Architecture

- **Affected Files**:
  - `src/models/wrestler/wrestler.py` [NEW]
  - `src/models/wrestler/moveset.py` [NEW]
- **Data Structures**:
  - `moveset.py`:
    - `class MoveType(str, Enum)`
    - `class Move(BaseModel)`
  - `wrestler.py`:
    - `class InRingSkill(BaseModel)`
    - `class Psychology(BaseModel)`
    - `class Backstage(BaseModel)`
    - `class Wrestler(BaseModel)`
- **Logic Flow**: 
  - The classes will purely serve as validated schemas at this stage (using Pydantic). 
  - `Wrestler.moveset` will use Pydantic `Set` validation to guarantee the uniqueness of assigned move IDs at the schema level.

## Work Order Refinement

- **To The Money Man**: 
  - When mapping these Pydantic models to SQLAlchemy later, use a many-to-many association table for `Wrestler <-> Move`. The `Move` model should correspond to a standalone `moves` table.
- **To The Booker**: 
  - No match engine math needed for this immediate sprint. When the simulation engine is built, it will fetch the full `Move` object from the library using the ID stored in the `Wrestler.moveset`.

## Referee Handbook (QA Scenarios)

- **Positive Tests**:
  - `test_create_valid_move`: Create a valid `Move`.
  - `test_create_valid_wrestler`: Create a valid `Wrestler` with a populated moveset list.
- **Negative Tests**:
  - `test_wrestler_stat_out_of_bounds`: Try to create a wrestler with 101 strength. Assert `ValidationError`.
  - `test_move_invalid_enum`: Try to create a move with `move_type="MAGIC"`. Assert `ValidationError`.
- **Edge Cases**:
  - `test_duplicate_moveset_ids_handled`: Try to assign `[move_id_1, move_id_1]` to a wrestler. Assert it evaluates to a set of length 1 (deduplicated automatically by Pydantic).
