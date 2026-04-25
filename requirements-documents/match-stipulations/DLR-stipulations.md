# Match Stipulations & Gimmick Logic — Detailed Logic Requirements (DLR)

## Traceability Table

| DLR ID | Linked HLR ID | Technical Requirement Explanation | Confirmation Test Case |
| :--- | :--- | :--- | :--- |
| *DLR-12.1.1* | *FR-12.1.0* | **`MatchStipulation` Enum**: `class MatchStipulation(str, Enum)` with members `STANDARD`, `HARDCORE`, `STEEL_CAGE`, `LADDER`, `SUBMISSION_ONLY`. Lives in `stipulation_logic_handler.py`. Adding new members requires no changes to any other file. | Verify `MatchStipulation.LADDER == "LADDER"`. Verify `BookingSheet` with no stipulation arg defaults to `STANDARD`. |
| *DLR-12.2.1* | *FR-12.2.0* | **`StipulationModifiers` Model**: Pydantic `BaseModel` with: `heat_multiplier: float`, `injury_chance_multiplier: float`, `stamina_cost_multiplier: float`, `damage_multiplier: float`, `star_rating_bonus: float`, `star_rating_penalty: float`, `production_cost: int`, `fatigue_multiplier: float`, `min_turn_bonus: int`, `difficulty_rating: int`, `required_skills: Dict[str, int]`, `danger_profile: List[str]`. | Verify model instantiates with all fields. Verify `STANDARD` has all multipliers at 1.0 and bonus/penalty at 0.0. |
| *DLR-12.3.1* | *FR-12.3.0* | **`calculate_execution_score(wrestler, modifiers) -> float`**: For each key in `modifiers.required_skills`, fetch wrestler stat via `_resolve_stat(wrestler, key)`. Compute `ratio = wrestler_stat / required_stat`. `raw_score = sum(ratios) / len(ratios)`. Return `raw_score`. If `required_skills` is empty, return `1.0`. | Verify wrestler with agility=70, required=70 → raw_score=1.0. Verify agility=140, required=70 → raw_score=2.0 (clamped in execution modifier calc). |
| *DLR-12.3.2* | *FR-12.3.0* | **`calculate_execution_modifier(raw_score, difficulty_rating) -> float`**: `modifier = (raw_score - 1.0) * difficulty_rating * 0.1`. Return unclamped float (clamping happens at application). | Verify raw=1.0, diff=4 → 0.0. Verify raw=1.5, diff=4 → +0.20. Verify raw=0.5, diff=4 → -0.20. |
| *DLR-12.3.3* | *FR-12.3.0* | **Applying the Execution Modifier to Star Rating**: `bonus = modifiers.star_rating_bonus * clamp(modifier, 0, 1)`. `penalty = modifiers.star_rating_penalty * clamp(-modifier, 0, 1)`. `final_star_rating = clamp(base_star_rating + bonus - penalty, 0.0, 5.0)`. The average execution modifier across ALL participants is used (not the worst performer). | Verify two wrestlers: one above, one below threshold → averaged modifier applied. Verify star rating clamped at 5.0. |
| *DLR-12.3.4* | *FR-12.3.0* | **Botch Trigger**: After computing `raw_score` per participant, if `any(raw_score < 0.6 for each participant)`: append `"{wrestler.name} botched a spot! The crowd groans."` to `play_by_play`. Also apply an **additional** `roll_for_injury()` call for that wrestler (targeted double-jeopardy). | Verify wrestler with agility=30 in a LADDER match (required=70 → ratio=0.43) triggers botch narrative. Verify injury roll is called twice for that wrestler. |
| *DLR-12.4.1* | *FR-12.4.0* | **`STIPULATION_MODIFIERS: Dict[MatchStipulation, StipulationModifiers]`**: Constant lookup dict in `stipulation_logic_handler.py`. Entries per HLR-12 Modifier Table. `get_modifiers(stipulation: MatchStipulation) -> StipulationModifiers` simply returns `STIPULATION_MODIFIERS[stipulation]`. | Verify `get_modifiers(MatchStipulation.HARDCORE).heat_multiplier == 2.0`. |
| *DLR-12.5.1* | *FR-12.5.0* | **`resolve_danger_event(wrestlers, modifiers, play_by_play, turn) -> Optional[UUID]`**: Called every 3 turns. If `modifiers.danger_profile` is non-empty: `random.choice(modifiers.danger_profile)` → append narrative. Select a random participant, call `roll_for_injury(wrestler)` → if injury returned, apply it. Return injured wrestler's UUID or `None`. | Verify danger event fires on turns 3, 6, 9. Verify no danger event fires on turn 2. Verify STANDARD has empty danger_profile → function returns immediately. |
| *DLR-12.6.1* | *FR-12.6.0* | **`validate_stipulation(stipulation, company_hype) -> None`**: `HYPE_GATES = {STEEL_CAGE: 100, LADDER: 80}`. If `stipulation in HYPE_GATES and company_hype < HYPE_GATES[stipulation]`: raise `ValueError(f"{stipulation} requires company_hype >= {HYPE_GATES[stipulation]}. Current: {company_hype}")`. | Verify STEEL_CAGE with hype=99 raises ValueError. Verify STEEL_CAGE with hype=100 passes. Verify HARDCORE with hype=10 passes (no gate). |
| *DLR-12.6.2* | *FR-12.6.0* | **`BookingSheet` update**: Add `stipulation: MatchStipulation = MatchStipulation.STANDARD`. Existing tests pass without specifying the field. | Verify existing booking tests unaffected. Verify `BookingSheet(..., stipulation=MatchStipulation.LADDER)` stores correctly. |
| *DLR-12.7.1* | *FR-12.7.0* | **Staleness Tracking**: Add `stipulation_usage: Dict[str, int] = Field(default_factory=dict)` to `Company`. On each event: if `company.stipulation_usage.get(stip, 0) + 1 > 3`: staleness is active. Increment counter regardless. On a different stipulation: **reset all counters to 0** then set the new one to 1. | Verify after 4 HARDCORE events: `stipulation_usage["HARDCORE"] == 4`. Verify after 3 HARDCORE + 1 STANDARD: `stipulation_usage["STANDARD"] == 1`, `"HARDCORE"` is reset to 0. |
| *DLR-12.8.1* | *FR-12.8.0* | **`financial_engine.py` — Production Cost**: `gate_revenue -= modifiers.production_cost`. Applied before staleness penalty calculation. | Verify STEEL_CAGE deducts $10,000. Verify STANDARD deducts $0. |
| *DLR-12.8.2* | *FR-12.8.0* | **`financial_engine.py` — Staleness Penalty**: `staleness = company.stipulation_usage.get(stip, 0) > 3`. `if staleness: gate_revenue = int(gate_revenue * 0.9)`. | Verify gate * 0.9 applied on 4th consecutive HARDCORE use. Verify 3rd use has no penalty. |

---

## Stat Resolution Map

`_resolve_stat(wrestler, key)` maps string keys to wrestler model attributes:

| Key | Model Path |
| :--- | :--- |
| `"strength"` | `wrestler.in_ring.strength` |
| `"agility"` | `wrestler.in_ring.agility` |
| `"stamina"` | `wrestler.in_ring.stamina` |
| `"work_rate"` | `wrestler.psychology.work_rate` |
| `"intelligence"` | `wrestler.psychology.intelligence` |
| `"selling"` | `wrestler.psychology.selling` |
| `"psychology"` | Average of `work_rate + intelligence + selling / 3` |

---

## Full Stipulation Modifier Reference

### STANDARD
```python
StipulationModifiers(heat_multiplier=1.0, injury_chance_multiplier=1.0,
  stamina_cost_multiplier=1.0, damage_multiplier=1.0,
  star_rating_bonus=0.0, star_rating_penalty=0.0,
  production_cost=0, fatigue_multiplier=1.0, min_turn_bonus=0,
  difficulty_rating=1, required_skills={}, danger_profile=[])
```

### HARDCORE
```python
StipulationModifiers(heat_multiplier=2.0, injury_chance_multiplier=2.5,
  stamina_cost_multiplier=1.5, damage_multiplier=1.5,
  star_rating_bonus=0.75, star_rating_penalty=0.75,
  production_cost=0, fatigue_multiplier=1.5, min_turn_bonus=0,
  difficulty_rating=2, required_skills={"strength": 55, "stamina": 50},
  danger_profile=["Unprotected chair shot", "Table spot", "Barbed wire contact"])
```

### STEEL_CAGE
```python
StipulationModifiers(heat_multiplier=1.5, injury_chance_multiplier=1.8,
  stamina_cost_multiplier=1.3, damage_multiplier=1.2,
  star_rating_bonus=0.5, star_rating_penalty=0.5,
  production_cost=10000, fatigue_multiplier=1.3, min_turn_bonus=5,
  difficulty_rating=3, required_skills={"strength": 65, "stamina": 70, "psychology": 60},
  danger_profile=["Cage wall slam", "High fall from cage roof", "Door escape attempt"])
```

### LADDER
```python
StipulationModifiers(heat_multiplier=2.0, injury_chance_multiplier=2.0,
  stamina_cost_multiplier=1.4, damage_multiplier=1.0,
  star_rating_bonus=1.0, star_rating_penalty=1.0,
  production_cost=5000, fatigue_multiplier=1.4, min_turn_bonus=3,
  difficulty_rating=4, required_skills={"agility": 70, "work_rate": 65},
  danger_profile=["Ladder suplex", "Dangerous ladder fall", "Crowd dive off ladder"])
```

### SUBMISSION_ONLY
```python
StipulationModifiers(heat_multiplier=1.2, injury_chance_multiplier=1.1,
  stamina_cost_multiplier=1.8, damage_multiplier=0.5,
  star_rating_bonus=0.5, star_rating_penalty=0.75,
  production_cost=0, fatigue_multiplier=1.2, min_turn_bonus=5,
  difficulty_rating=3, required_skills={"work_rate": 75, "intelligence": 70},
  danger_profile=["Joint hyperextension", "Choke held too long"])
```

---

## Technical Specs & Architecture

### `stipulation_logic_handler.py` — Function Signatures

```python
def get_modifiers(stipulation: MatchStipulation) -> StipulationModifiers: ...
def validate_stipulation(stipulation: MatchStipulation, company_hype: float) -> None: ...
def calculate_execution_score(wrestler: Wrestler, modifiers: StipulationModifiers) -> float: ...
def calculate_execution_modifier(raw_score: float, difficulty_rating: int) -> float: ...
def resolve_danger_event(wrestlers: Dict[UUID, Wrestler], modifiers: StipulationModifiers,
                         play_by_play: List[str], turn: int) -> Optional[UUID]: ...
def _resolve_stat(wrestler: Wrestler, key: str) -> float: ...
```

### `match_simulator.py` — Integration Order

Modifiers must be applied in this exact sequence to avoid stacking errors:

1. **Fetch**: `modifiers = get_modifiers(booking_sheet.stipulation)` at function entry.
2. **Validate**: `validate_stipulation(booking_sheet.stipulation, company_hype)` if company is provided.
3. **Turn floor**: `turn_limit = max(turn_limit, turn_limit + modifiers.min_turn_bonus)`.
4. **Per-spot (inside loop)**: Apply `heat_multiplier`, `damage_multiplier`, `stamina_cost_multiplier`.
5. **Per-turn danger check (inside loop)**: `if turn % 3 == 0: resolve_danger_event(...)`.
6. **Post-loop execution check**: Compute `raw_score` and `execution_modifier` per participant, average them.
7. **Botch check**: Flag any participant with `raw_score < 0.6`.
8. **Star rating**: Add `bonus - penalty` from execution modifier, then clamp 0–5.
9. **Fatigue**: Apply `fatigue_multiplier` to `fatigue_gain`.
10. **Injury**: Apply `injury_chance_multiplier` to `calculate_injury_chance()`.

---

## Work Order Refinement

- **To The Booker**:
  - Build `stipulation_logic_handler.py` first — it has zero external dependencies on other engine files.
  - `_resolve_stat` should raise `KeyError` with a clear message if an unknown key is passed — this is the primary failure mode during development.
  - The `calculate_execution_score` must handle `required_skills = {}` by returning `1.0` (no requirement = always passes).
  - The `company_hype` param to `validate_stipulation` is optional (`= None`). If `None`, skip the gate check silently.

- **To The Money Man**:
  - Production cost and staleness are deducted in `financial_engine.py` — the simulator itself does NOT touch finances.
  - Pass `booking_sheet.stipulation` into `process_event_finances` as an argument, or fetch it from the `Event` model if events will carry match records.

---

## Referee Handbook (QA Scenarios)

- **Positive**: LADDER match, all wrestlers agility=90, work_rate=80 → bonus applied, star rating above base.
- **Positive**: HARDCORE match, strength=60, stamina=55 → slightly above threshold → small bonus.
- **Negative**: LADDER match, wrestler agility=30 → `raw_score=0.43 < 0.6` → botch fires, double injury roll.
- **Negative**: STEEL_CAGE on company with hype=50 → `ValueError` raised immediately.
- **Edge**: STANDARD match → `required_skills={}` → `raw_score=1.0`, no bonus or penalty.
- **Edge**: `star_rating = 4.8 + 0.5 bonus = 5.3` → clamped to `5.0`.
- **Staleness**: 4 consecutive HARDCORE events → gate × 0.9 on event 4.
- **Staleness Reset**: HARDCORE × 3 then STANDARD → HARDCORE counter resets to 0.
