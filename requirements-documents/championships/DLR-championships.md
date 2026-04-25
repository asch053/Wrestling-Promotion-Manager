# Championship Gold & Legacy - Detailed Logic Requirements (DLR)

## Traceability Table

| DLR ID | Linked HLR ID | Technical Requirement Explanation | Confirmation Test Case |
| :--- | :--- | :--- | :--- |
| *DLR-9.1.1* | *FR-9.1.0* | Implement `Championship` model: `id: UUID`, `name: str`, `prestige: int = 50` (0-100), `championship_type: ChampionshipType` (SINGLES/TAG_TEAM), `tier: ChampionshipTier` (WORLD/MID_CARD), `is_active: bool = True`, `current_holder: Optional[UUID] = None`, `title_history: List[TitleReign]`. | Verify instantiation and defaults. |
| *DLR-9.1.2* | *FR-9.1.0* | Implement `ChampionshipType(str, Enum)` with `SINGLES`, `TAG_TEAM`. Implement `ChampionshipTier(str, Enum)` with `WORLD`, `MID_CARD`. | Verify enum values. |
| *DLR-9.2.1* | *FR-9.2.0* | Implement `TitleReign(BaseModel)`: `holder_id: UUID`, `holder_name: str`, `defenses: int = 0`, `start_event: str`, `end_event: Optional[str] = None`. | Verify instantiation. |
| *DLR-9.3.1* | *FR-9.3.0* | In `company.py`, update `calculate_current_hype()` to add `sum(c.prestige * 2 for c in championships if c.is_active and c.tier == WORLD)`. Update `calculate_current_excitement()` to add `sum(c.prestige for c in championships if c.is_active and c.tier == MID_CARD)`. | Verify a 100-prestige WORLD title adds 200 to Company Hype. |
| *DLR-9.4.1* | *FR-9.4.0* | Implement `calculate_saturation_penalty(company)` in `championship_manager.py`. `active_count = len([c for c in company.championships if c.is_active])`. `penalty = max(0, (active_count - 4) * 0.05 * company.calculate_current_excitement())`. Return as int. | Verify 6 titles with 100 excitement = `(6-4) * 0.05 * 100 = 10` penalty. Verify 4 titles = 0 penalty. |
| *DLR-9.5.1* | *FR-9.5.0* | `award_title(championship, wrestler_id, wrestler_name, event_name)`: Set `current_holder`, append new `TitleReign` to history. | Verify holder is set and history grows. |
| *DLR-9.5.2* | *FR-9.5.0* | `vacate_title(championship, event_name)`: Set `current_holder = None`, close the current reign's `end_event`. | Verify holder is None and reign is closed. |
| *DLR-9.5.3* | *FR-9.5.0* | `retire_title(championship)`: Set `is_active = False`, vacate if held. History preserved. | Verify `is_active` is False but history intact. |
| *DLR-9.5.4* | *FR-9.5.0* | `unretire_title(championship)`: Set `is_active = True`. Prestige returns at full historical value. | Verify un-retired title retains prestige. |
| *DLR-9.6.1* | *FR-9.6.0* | `update_prestige(championship, star_rating)`: `delta = int(round((star_rating - 3.0) * 5))`. `championship.prestige = clamp(prestige + delta, 0, 100)`. If `current_holder`, increment `defenses` on the current reign. | Verify 5-star match adds +10 prestige. Verify 1-star drops -10. |
| *DLR-9.7.1* | *FR-9.7.0* | In `morale_engine.py`, add championship hunger check. If `ego > 70` and wrestler holds no title: `-5` morale. If additionally `hype > 80` and no WORLD-tier title: additional `-5`. | Verify high-ego titleless wrestler loses 5 morale. Verify high-hype loses 10 total. |
| *DLR-9.8.1* | *FR-9.8.0* | In `financial_engine.py`, when calculating merch per wrestler, check if wrestler is `current_holder` of any active championship. If so: `w_merch = base_merch * (1 + championship.prestige / 100)`. If holding multiple titles, use the highest prestige. | Verify champion with 100-prestige belt gets 2x merch. |
| *DLR-9.9.1* | *FR-9.9.0* | Add `championship_id: Optional[UUID] = None` to `BookingSheet`. | Verify field exists and is optional. |

## Technical Specs & Architecture

- **Affected Files**:
  - `src/models/promotion/championship.py` [NEW]
  - `src/engine/championship_manager.py` [NEW]
  - `src/models/promotion/booking/booking_sheet.py` [MODIFY]
  - `src/models/promotion/company.py` [MODIFY]
  - `src/engine/match_simulator.py` [MODIFY]
  - `src/engine/financial_engine.py` [MODIFY]
  - `src/engine/morale_engine.py` [MODIFY]

- **Data Structures**:
  - `championship.py`:
    - `class ChampionshipType(str, Enum)`: SINGLES, TAG_TEAM
    - `class ChampionshipTier(str, Enum)`: WORLD, MID_CARD
    - `class TitleReign(BaseModel)`: holder_id, holder_name, defenses, start_event, end_event
    - `class Championship(BaseModel)`: id, name, prestige, championship_type, tier, is_active, current_holder, title_history
  - `company.py`:
    - Add `championships: List[Championship] = Field(default_factory=list)`
  - `booking_sheet.py`:
    - Add `championship_id: Optional[UUID] = None`

- **Logic Flow**:
  1. Player creates a `Championship` and adds it to `company.championships`.
  2. Player books a title match by setting `championship_id` on the `BookingSheet`.
  3. Post-match, `championship_manager.update_prestige()` adjusts the belt's prestige based on star rating.
  4. If the title changes hands, `award_title()` is called with the new holder. The old reign is closed.
  5. `financial_engine.py` checks if wrestlers are champions and applies the merch multiplier.
  6. `morale_engine.py` checks "The Hunger" — titleless high-ego wrestlers lose morale.
  7. `calculate_saturation_penalty()` is called during financial processing to reduce gate revenue.

- **`check_hierarchy_violation(wrestler, championship, company)`**: Returns `True` if booking a wrestler for a title match would be a "violation" of the hierarchy. A violation occurs if:
  - WORLD title match and `wrestler.popularity.hype < 60` (wrestler is too low on the card).
  - This is a **warning**, not a block — the player can still book it, but it should devalue the belt (apply `-5` prestige penalty if the match happens).

## Referee Handbook (QA Scenarios)

- **Championship Model Tests**:
  - `test_championship_creation`: Verify Championship with all fields instantiates correctly.
  - `test_title_reign_tracking`: Award title, verify history grows. Vacate, verify reign is closed.
- **Prestige Tests**:
  - `test_prestige_5_star_defense`: 5-star match adds +10 prestige and increments defenses.
  - `test_prestige_1_star_tank`: 1-star match drops -10 prestige.
- **Saturation Tests**:
  - `test_saturation_penalty`: 6 active titles with 100 excitement = 10 penalty. 4 titles = 0.
  - `test_retirement_reduces_saturation`: Retire one of 6 titles. Verify penalty drops.
- **Morale Tests**:
  - `test_hunger_titleless_ego`: High-ego wrestler without title loses 5 morale.
  - `test_hunger_world_title`: High-hype wrestler without WORLD title loses 10 total.
- **Financial Tests**:
  - `test_champion_merch_bonus`: Champion with 100-prestige belt earns 2x base merch.
