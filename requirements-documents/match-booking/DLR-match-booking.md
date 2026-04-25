# Match Booking Sheet - Detailed Logic Requirements (DLR)

## Traceability Table

| DLR ID | Linked HLR ID | Technical Requirement Explanation | Confirmation Test Case |
| :--- | :--- | :--- | :--- |
| *DLR-2.1.1* | *FR-2.1.0* | Implement `MatchType` as an Enum (e.g., `ONE_ON_ONE`, `TAG_TEAM`, `TRIPLE_THREAT`). | Verify Enum instantiation. |
| *DLR-2.1.2* | *FR-2.1.0* | Implement `BookingSheet` Pydantic model with `match_type` and `participants` (a List of UUIDs). | Instantiate `BookingSheet` with a valid participants list. |
| *DLR-2.2.1* | *FR-2.2.0* | Implement `ScriptingStyle` as an Enum (`STRICT`, `AUDIBLE`, `CALLED_IN_RING`). | Verify Enum instantiation. |
| *DLR-2.3.1* | *FR-2.3.0* | Implement `Runsheet` Pydantic model. `BookingSheet` must have an optional `expected_runsheet` field. | Instantiate `BookingSheet` with and without a runsheet. |
| *DLR-2.3.2* | *FR-2.3.0* | Use Pydantic `@model_validator(mode='after')` to enforce: If `scripting_style` is `STRICT` or `AUDIBLE`, `expected_runsheet` MUST NOT be None. | Try to create `STRICT` sheet without runsheet -> assert `ValidationError`. |
| *DLR-2.4.1* | *FR-2.4.0* | Add `designated_winner` (UUID) to `BookingSheet`. Use `@model_validator` to enforce that `designated_winner` exists in the `participants` list. | Try to create sheet where winner is not in participants -> assert `ValidationError`. |

## Technical Specs & Architecture

- **Affected Files**:
  - `src/models/promotion/booking/booking_sheet.py` [NEW]
  - `src/models/promotion/booking/runsheet.py` [NEW]
- **Data Structures**:
  - `runsheet.py`:
    - `class Runsheet(BaseModel)`: Contains a `spots` attribute which is a `List[UUID]` (representing the sequence of moves/spots).
  - `booking_sheet.py`:
    - `class MatchType(str, Enum)`
    - `class ScriptingStyle(str, Enum)`
    - `class BookingSheet(BaseModel)`: Contains the core fields. It utilizes a `@model_validator(mode='after')` to execute the complex cross-field validation rules (e.g., checking if the winner is in the match).
- **Logic Flow**: 
  - The `@model_validator` intercepts the object creation. It will raise a ValueError if the business rules aren't met, ensuring the simulation engine only ever receives logically sound booking sheets.

## Work Order Refinement

- **To The Money Man**: 
  - Ensure that when persisting `BookingSheet` to the database, `participants` maps to a many-to-many relationship with the wrestlers table. `scripting_style` and `match_type` can be stored as standard strings via the Enum values.
- **To The Booker**: 
  - When building the match simulation engine, you will pull the `expected_runsheet` spots from this `BookingSheet` object to dictate the simulation flow if the match is `STRICT`.

## Referee Handbook (QA Scenarios)

- **Positive Tests**:
  - `test_valid_called_in_ring_booking`: Create a booking with `CALLED_IN_RING` and `expected_runsheet=None`.
  - `test_valid_strict_booking`: Create a `STRICT` booking WITH a populated runsheet.
  - `test_valid_winner`: The `designated_winner` is one of the UUIDs inside the `participants` list.
- **Negative Tests**:
  - `test_strict_booking_missing_runsheet`: Create `STRICT` with `expected_runsheet=None`. Assert `ValidationError` indicating runsheet is required.
  - `test_audible_booking_missing_runsheet`: Create `AUDIBLE` with `expected_runsheet=None`. Assert `ValidationError`.
  - `test_invalid_winner`: Set `designated_winner` to a UUID that is NOT in `participants`. Assert `ValidationError` indicating the winner isn't in the match.
