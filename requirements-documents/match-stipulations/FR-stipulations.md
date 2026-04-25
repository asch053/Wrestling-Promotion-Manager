# Match Stipulations & Gimmick Logic — Executive Summary (v1.2)

Every title change has a stage. Every blood feud needs a stage worth dying on. This feature moves the simulation beyond standard singles bouts and introduces high-stakes gimmick matches that fundamentally alter the physics of the Match Engine.

> **v1.2 Design Note**: Stipulation matches are now **skill-gated**. Each stipulation defines `required_skills` (minimum stat thresholds), a `difficulty_rating` (1-5), and a `danger_profile` (a list of specific risk events). Skilled wrestlers rise to the occasion; unskilled ones botch, bleed, and get carried out. The difference between a LADDER classic and a LADDER disaster is the people in it.

---

## High-Level Requirements (HLR) Document

**Feature ID**: F-012
**Feature Name**: Match Stipulations & Gimmick Logic
**Description**: Introduces a `MatchStipulation` enum with per-stipulation modifier objects covering heat, injury, stamina, production cost, and a new **Execution Difficulty** system. Each stipulation defines required skill thresholds; wrestler skill relative to those thresholds drives the quality ceiling and danger floor of the match.

---

**User Stories**:
- As a Booker, I want to be warned if I book a LADDER match with wrestlers who don't have the required Agility — it should hurt the star rating and increase the chance of a botch.
- As a Booker, I want to see a SUBMISSION_ONLY match between two technical wrestlers produce a clinic, but the same match with brawlers should be a mess.
- As a Booker, I want to know the specific dangers of each stipulation (e.g., "Ladder fall risk", "Cage wall collision") before booking.
- As a Booker, I need to manage stipulation frequency — overusing gimmick matches should cause fan burnout.
- As a Money Man, I need to see Production Costs deducted from the event's financial report.
- As a Referee (QA), I want the Execution Check to be deterministic and testable given fixed stats.

---

**Functional Requirements**:

- **FR-12.1.0 — MatchStipulation Enum (Extensible)**:
  - `STANDARD`, `HARDCORE`, `STEEL_CAGE`, `LADDER`, `SUBMISSION_ONLY`.
  - Stored as a `str` enum for serialisation compatibility.
  - New stipulations can be appended without breaking existing logic.

- **FR-12.2.0 — StipulationModifiers Object**:
  Each stipulation carries a `StipulationModifiers` data object with:
  - `heat_multiplier: float`
  - `injury_chance_multiplier: float`
  - `stamina_cost_multiplier: float`
  - `damage_multiplier: float`
  - `star_rating_bonus: float` — maximum bonus added if all wrestlers **meet** the required skills.
  - `star_rating_penalty: float` — maximum penalty subtracted if wrestlers **fall below** required skills.
  - `production_cost: int`
  - `fatigue_multiplier: float`
  - `min_turn_bonus: int`
  - `difficulty_rating: int` — 1 (easy) to 5 (career-defining). Scales the skill gap effect.
  - `required_skills: Dict[str, int]` — minimum stat values needed to execute the stipulation cleanly (e.g., `{"agility": 70, "work_rate": 60}`).
  - `danger_profile: List[str]` — named dangers specific to this stipulation that appear in the play-by-play and increase targeted injury types.

- **FR-12.3.0 — Execution Check (The Heart of the System)**:
  - At the start of `simulate_match`, compute an `execution_score` for each participant.
  - **Formula**: For each required skill, compute `participant_stat / required_stat`. Average across all required skills → `raw_score` (clamped 0-2.0, where 1.0 = meets requirements exactly).
  - **Modifier**: `execution_modifier = (raw_score - 1.0) * difficulty_rating * 0.1`
    - Positive = skilled, bonus to star rating.
    - Negative = unskilled, penalty to star rating + increased injury chance.
  - Apply `star_rating_bonus * clamp(execution_modifier, 0, 1)` to the final star rating.
  - Apply `star_rating_penalty * clamp(-execution_modifier, 0, 1)` as a deduction.
  - If any participant's `raw_score < 0.6`, trigger a "Botch" narrative event.

- **FR-12.4.0 — Stipulation Modifier Values**:

  | Stipulation | Heat | Injury | Stamina | Damage | Max Star Bonus | Max Star Penalty | Cost | Fatigue | Min Turns | Difficulty | Required Skills |
  |:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:--- |
  | `STANDARD`        | 1.0 | 1.0 | 1.0 | 1.0 | +0.0  | -0.0  | $0      | 1.0 | 0 | 1 | None |
  | `HARDCORE`        | 2.0 | 2.5 | 1.5 | 1.5 | +0.75 | -0.75 | $0      | 1.5 | 0 | 2 | `{strength: 55, stamina: 50}` |
  | `STEEL_CAGE`      | 1.5 | 1.8 | 1.3 | 1.2 | +0.5  | -0.5  | $10,000 | 1.3 | 5 | 3 | `{strength: 65, stamina: 70, psychology: 60}` |
  | `LADDER`          | 2.0 | 2.0 | 1.4 | 1.0 | +1.0  | -1.0  | $5,000  | 1.4 | 3 | 4 | `{agility: 70, work_rate: 65}` |
  | `SUBMISSION_ONLY` | 1.2 | 1.1 | 1.8 | 0.5 | +0.5  | -0.75 | $0      | 1.2 | 5 | 3 | `{work_rate: 75, intelligence: 70}` |

- **FR-12.5.0 — Danger Profiles**:

  | Stipulation | Danger Events |
  |:---|:---|
  | `HARDCORE`     | "Unprotected chair shot", "Table spot", "Barbed wire contact" |
  | `STEEL_CAGE`   | "Cage wall slam", "High fall from cage roof", "Door escape attempt" |
  | `LADDER`       | "Ladder suplex", "Dangerous ladder fall", "Crowd dive off ladder" |
  | `SUBMISSION_ONLY` | "Joint hyperextension", "Choke held too long" |

  - Danger events are selected randomly from the profile during the simulation loop (1 event per 3 turns).
  - Each danger event adds `+heat * 1.5` but also triggers a targeted injury roll (in addition to the base injury roll).

- **FR-12.6.0 — Booking Integration**:
  - `BookingSheet` gains `stipulation: MatchStipulation = MatchStipulation.STANDARD`.
  - Hype gates: `STEEL_CAGE` requires `company_hype >= 100`, `LADDER` requires `company_hype >= 80`.
  - **Gate Type**: Hard block (raises `ValueError`) to prevent devaluing the product on a small stage.

- **FR-12.7.0 — Staleness / Fan Burnout**:
  - `Company` tracks `stipulation_usage: Dict[str, int]`.
  - Using the same gimmick match **more than 3 consecutive events** applies a **-10% gate revenue penalty**.
  - Counter resets when a different stipulation is booked.

- **FR-12.8.0 — Financial Integration**:
  - `production_cost` deducted from event gate revenue.
  - Staleness penalty applied to gate.

---

**Acceptance Criteria**:
- A LADDER match between two wrestlers with Agility=90, Work Rate=80 should score higher than STANDARD.
- The same LADDER match with Agility=40 wrestlers should score *lower* than STANDARD and trigger a botch event.
- A STEEL_CAGE booking on company_hype < 100 raises a `ValueError`.
- Using HARDCORE 4 events in a row reduces gate by 10%.
- Danger events appear in the play-by-play narrative.

---

## Logic Blueprint

- **Execution Score (per participant)**: `avg(stat / required_stat for each required_skill)`
- **Execution Modifier**: `(avg_score - 1.0) * difficulty_rating * 0.1`
- **Star Bonus**: `star_rating_bonus * clamp(execution_modifier, 0, 1)`
- **Star Penalty**: `star_rating_penalty * clamp(-execution_modifier, 0, 1)`
- **Botch Trigger**: `any participant raw_score < 0.6`
- **Staleness Gate**: `if stipulation_usage[stip] > 3: gate *= 0.9`

## File Impact List

- `[NEW]` `src/engine/stipulation_logic_handler.py`
- `[MODIFY]` `src/models/promotion/booking/booking_sheet.py`
- `[MODIFY]` `src/models/promotion/company.py`
- `[MODIFY]` `src/engine/match_simulator.py`
- `[MODIFY]` `src/engine/financial_engine.py`
- `[NEW]` `tests/engine/test_stipulations.py`

## Agent Assignments

- **To Road Agent**: Draft the DLR with precise function signatures for `get_modifiers()`, `validate_stipulation()`, `calculate_execution_score()`, and `resolve_danger_event()`. Specify the order of modifier application in the simulator loop.
- **To The Booker**: *(Upon DLR approval)* Implement all files listed above.
- **To The Referee**: *(Upon implementation)* Write `test_stipulations.py` covering execution score math, botch triggers, staleness, and financial deductions.
