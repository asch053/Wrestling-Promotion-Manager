# Championship Gold & Legacy - Executive Summary

Championships are the currency of professional wrestling. They define your hierarchy, drive your storylines, and separate the main eventers from the curtain jerkers. But too many belts dilute the product, and a poorly-booked champion tanks the prestige of the gold itself. This feature introduces player-created Championships with full history tracking, a Title Saturation penalty, and deep integration with Morale, Finances, and Match Simulation.

## High-Level Requirements (HLR) Document

**Feature ID**: F-009
**Feature Name**: Championship Gold & Legacy
**Description**: Implement a `Championship` model that players can create with custom names, types, and tiers. Championships track full title histories (past holders and reign lengths). The system enforces a Title Saturation penalty when too many belts are active, integrates with the Morale system (high-ego wrestlers need gold), and drives Prestige changes based on match quality.

**User Stories**:
- As a Booker, I want to create custom Championships with a `name`, `type` (SINGLES/TAG_TEAM), and `tier` (WORLD/MID_CARD).
- As a Booker, I want every title to track its complete `TitleHistory` — who held it, when, and for how long.
- As a Booker, I want WORLD-tier titles to act as massive multipliers for Company Hype, while MID_CARD titles boost Crowd Excitement.
- As the Money Man, I want active champions to receive a Merch Bonus reflecting the prestige of their belt.
- As a Booker, I need to be warned when I have too many active titles. Every title above the threshold should penalize my Company Excitement and Gate Revenue.
- As a Booker, I want to "Retire" a belt, removing it from the saturation count but preserving its legacy history.
- As a Booker, I want to "Un-retire" a legendary belt, bringing it back with its full history and prestige intact.
- As a Booker, I want high-ego wrestlers to suffer morale decay if they aren't holding a title at or above their perceived tier.
- As a Referee, I want the prestige of a belt to increase after a high-star-rating defense and decrease after a screwjob or bad match.

**Functional Requirements**:
- **FR-9.1.0 - Championship Model**: Create `Championship` with `id`, `name`, `prestige` (0-100, default 50), `championship_type` (SINGLES/TAG_TEAM), `tier` (WORLD/MID_CARD), `is_active` (bool), `current_holder: Optional[UUID]`, `title_history: List[TitleReign]`.
- **FR-9.2.0 - Title History**: Create `TitleReign` tracking `holder_id: UUID`, `holder_name: str`, `defenses: int`, `start_event: str`, `end_event: Optional[str]`.
- **FR-9.3.0 - Hierarchy Logic**: WORLD titles contribute `prestige * 2` to Company Hype calculation. MID_CARD titles contribute `prestige * 1` to Company Excitement.
- **FR-9.4.0 - Title Saturation Penalty**: Define `MAX_OPTIMAL_TITLES = 4`. For every active title above this threshold: `Penalty = (Active_Titles - 4) * 0.05 * Company_Excitement`. Penalty is subtracted from Gate Revenue.
- **FR-9.5.0 - Retirement & Un-Retirement**: Retired titles set `is_active = False`. They stop counting toward saturation but retain their history. Un-retiring restores `is_active = True`.
- **FR-9.6.0 - Prestige Delta**: After a title match, adjust prestige: `prestige_delta = (star_rating - 3.0) * 5`. A 5-star defense adds +10 prestige. A 1-star defense drops -10.
- **FR-9.7.0 - Morale Integration (The Hunger)**: In `morale_engine.py`, high-ego wrestlers (`ego > 70`) who are not holding ANY title suffer `-5` morale per event. High-ego wrestlers not holding a WORLD-tier title (when they have `hype > 80`) suffer an additional `-5`.
- **FR-9.8.0 - Champion Merch Bonus**: In `financial_engine.py`, active champions receive a merch multiplier: `champion_merch = base_merch * (1 + prestige / 100)`. A wrestler holding a 100-prestige belt earns 2x merch.
- **FR-9.9.0 - BookingSheet Integration**: Add `championship_id: Optional[UUID]` to `BookingSheet` to designate title matches.

**Acceptance Criteria**:
- A company with 6 active titles suffers a measurable gate revenue penalty compared to 4 titles.
- Retiring a title reduces the saturation count immediately.
- A 5-star title defense increases the belt's prestige.
- A high-ego wrestler without gold loses morale every event.
- A champion holding a 100-prestige belt generates significantly more merch revenue.

## Logic Blueprint

- **Saturation Penalty**: `max(0, (active_titles - 4) * 0.05 * company_excitement)`
- **Prestige Delta**: `(star_rating - 3.0) * 5` (clamped 0-100)
- **Champion Merch**: `base_merch * (1 + prestige / 100)`
- **Hierarchy Hype**: WORLD = `prestige * 2` added to Company Hype. MID_CARD = `prestige * 1` added to Company Excitement.
- **The Hunger**: `-5` morale if ego > 70 and no title. Additional `-5` if hype > 80 and no WORLD title.

## File Impact List

- `[NEW]` `src/models/promotion/championship.py`
- `[NEW]` `src/engine/championship_manager.py`
- `[MODIFY]` `src/models/promotion/booking/booking_sheet.py`
- `[MODIFY]` `src/models/promotion/company.py`
- `[MODIFY]` `src/engine/match_simulator.py`
- `[MODIFY]` `src/engine/financial_engine.py`
- `[MODIFY]` `src/engine/morale_engine.py`

## Agent Assignments

- **To Road Agent**: Draft the DLR. Define the exact Pydantic schemas, the `check_hierarchy_violation()` function, and the saturation penalty integration points.
- **To The Booker**: *(Future Step)* Build `championship_manager.py`. Update `match_simulator.py` to handle title match prestige deltas.
- **To The Referee**: *(Future Step)* Write tests proving saturation penalties, prestige shifts, and morale hunger mechanics.
