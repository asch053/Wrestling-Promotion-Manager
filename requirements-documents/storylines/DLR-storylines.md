# Storylines & Long-Term Booking - Detailed Logic Requirements (DLR)

## Traceability Table

| DLR ID | Linked HLR ID | Technical Requirement Explanation | Confirmation Test Case |
| :--- | :--- | :--- | :--- |
| *DLR-7.1.1* | *FR-7.1.0* | Implement `Storyline` model tracking `id`, `name`, `participants: List[UUID]`, `excitement: int = 50`, `is_active: bool = True`, `planned_outcome: PlannedOutcome`, `target_wrestler: Optional[UUID]`. | Verify instantiation and defaults. |
| *DLR-7.2.1* | *FR-7.2.0* | Implement `PlannedOutcome` Enum (`TURN_FACE`, `TURN_HEEL`, `PUSH_STAR`, `BUILD_RIVALRY`). | Verify Enum values. |
| *DLR-7.3.1* | *FR-7.3.0* | Refactor `BookingSheet` to include `storyline_id: Optional[UUID]`. Update `match_simulator.py` to accept `storyline_excitement`. Set `MatchState.crowd_excitement` to `storyline_excitement` instead of `50`. | Verify matches with storyline start at storyline's excitement. |
| *DLR-7.3.2* | *FR-7.3.0* | In `match_simulator.py`, return `storyline_delta` in `MatchReport` (formula: `(star_rating - 3.0) * 5`). | Verify 5-star match returns `+10` storyline delta. |
| *DLR-7.4.1* | *FR-7.4.0* | Implement `decay_inactive_storylines(company, event)` in `storyline_manager.py` which decreases `excitement` by 10 for active storylines not referenced in the `Event.match_reports`. | Verify neglected storyline loses 10 excitement. |
| *DLR-7.5.1* | *FR-7.5.0* | Implement `conclude_storyline(company, storyline, winner_id)`. "Cashes in" excitement. Adds `storyline.excitement / 10` (e.g. +10) to `company.base_excitement_modifier` (which affects gate). Marks `is_active = False`. | Verify Payoff adds excitement to Company. |
| *DLR-7.5.2* | *FR-7.5.0* | **Payoff Logic (Fluid Alignment Aware)**: `TURN_HEEL` no longer sets a static `alignment` field. Instead, it injects a massive `Heat` spike (+40) and drains `Pop` (-30) on the `target_wrestler`, causing their dynamic `alignment` property to naturally evaluate as `HEEL`. It also deletes friendships with wrestlers who are currently dynamically `FACE` and sets rivalry to 100. `TURN_FACE` does the inverse (Pop +40, Heat -30). `PUSH_STAR` adds `storyline.excitement / 2` to `target_wrestler.popularity.hype`. `BUILD_RIVALRY` sets mutual rivalry to 100 between all participants. | Verify `TURN_HEEL` causes the target's dynamic alignment to shift to `HEEL`. Verify `PUSH_STAR` massively boosts Hype. |

## Technical Specs & Architecture

- **Affected Files**:
  - `src/models/promotion/storyline.py` [NEW]
  - `src/models/promotion/booking/booking_sheet.py` [MODIFY]
  - `src/engine/match_simulator.py` [MODIFY]
  - `src/engine/models/match_report.py` [MODIFY]
  - `src/engine/storyline_manager.py` [NEW]
  - `src/models/promotion/company.py` [MODIFY]

- **Data Structures**:
  - `storyline.py`:
    - `class PlannedOutcome(str, Enum)`
    - `class Storyline(BaseModel)`
  - `match_report.py`:
    - Add `storyline_delta: int = 0`
    - Add `storyline_id: Optional[UUID] = None`
  - `booking_sheet.py`:
    - Add `storyline_id: Optional[UUID] = None`
  - `company.py`:
    - Add `storylines: List[Storyline] = Field(default_factory=list)`

- **Logic Flow**: 
  1. Booker creates a `Storyline` in `company.storylines`.
  2. Booker creates a `BookingSheet`, assigning the `storyline_id`.
  3. `simulate_match()` receives the booking sheet. If a `storyline_id` is present, it fetches the current storyline excitement and uses it as the initial `crowd_excitement` (bypassing the dead crowd `50` start).
  4. The simulator returns `storyline_delta` in the `MatchReport`.
  5. Post-match, `storyline_manager.py` applies the `storyline_delta` to the `Storyline.excitement` (bounded 0-100).
  6. End of Event: `decay_inactive_storylines` is called.
  7. **Payoff (Fluid Alignment)**: Booker calls `conclude_storyline`. Instead of flipping a static Alignment field, the engine manipulates the Pop/Heat balance directly:
     - `TURN_HEEL`: `target.popularity.heat = min(100, heat + 40)`, `target.popularity.pop = max(0, pop - 30)`. This causes the dynamic `alignment` property to naturally shift to `HEEL`. Friendships with current Faces are destroyed, rivalries set to 100.
     - `TURN_FACE`: `target.popularity.pop = min(100, pop + 40)`, `target.popularity.heat = max(0, heat - 30)`. Dynamic alignment naturally shifts to `FACE`.
     - `PUSH_STAR`: `target.popularity.hype += storyline.excitement / 2`.
     - `BUILD_RIVALRY`: Mutual rivalry set to 100 between all participants.
  8. `is_active` becomes `False`.

## Referee Handbook (QA Scenarios)

- **Match Simulator Tests**:
  - `test_storyline_starting_heat`: Verify passing a 90-excitement storyline forces the match simulation to begin at 90 excitement instead of 50.
  - `test_storyline_delta_progression`: Verify a 5-star match correctly returns a `+10` storyline delta, and a 1-star match returns negative.
- **Storyline Manager Tests**:
  - `test_decay_inactive_storylines`: Verify that when an event concludes, any active storylines not represented in the event lose 10 excitement.
  - `test_payoff_turn_heel`: Conclude a `TURN_HEEL` storyline. Assert the target wrestler's `popularity.heat` increased by 40 and `popularity.pop` decreased by 30. Assert their dynamic `alignment` property now evaluates as `HEEL`. Assert friendships with Faces are gone and rivalries are created.
  - `test_payoff_turn_face`: Conclude a `TURN_FACE` storyline. Assert Pop increased, Heat decreased, and dynamic alignment now evaluates as `FACE`.
  - `test_payoff_push_star`: Conclude a `PUSH_STAR` storyline with 100 excitement. Assert the target wrestler receives `+50` to their `hype` stat.
