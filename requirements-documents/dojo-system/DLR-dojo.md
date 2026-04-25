# Dojo, Scouting & Talent Recruitment - Detailed Logic Requirements (DLR)

## Traceability Table

| DLR ID | Linked HLR ID | Technical Requirement Explanation | Confirmation Test Case |
| :--- | :--- | :--- | :--- |
| *DLR-11.1.1* | *FR-11.1.0* | **`Dojo` Model**: Pydantic model with fields: `id: UUID`, `name: str`, `style: DojoStyle`, `prestige_stars: int = Field(ge=0, le=5, default=1)`, `equipment_level: int = Field(ge=1, le=5, default=1)`, `appeal: int = Field(ge=0, le=100, default=50)`, `xp: int = 0`, `students: List[Wrestler] = []`, `manager: DojoManager`, `graduates: List[UUID] = []`. | Verify Dojo instantiates with all defaults. Verify `prestige_stars` rejects values > 5. |
| *DLR-11.2.1* | *FR-11.2.0* | **`DojoManager` Model**: Pydantic model with `name: str`, `scouting_skill: int = Field(ge=0, le=100)`, `training_skill: int = Field(ge=0, le=100)`. | Verify model rejects `scouting_skill > 100`. |
| *DLR-11.3.1* | *FR-11.3.0* | **`DojoStyle` Enum (Extensible)**: `STRONG_STYLE`, `TECHNICAL`, `LUCHA`, `BRAWLER`, `SHOWMAN`. Stored as `str` enum for JSON serialization compatibility. Adding new members to this Enum requires no changes to existing logic. | Verify `DojoStyle.LUCHA` serializes to `"LUCHA"`. |
| *DLR-11.4.1* | *FR-11.4.0* | **`WrestlerStyle` Enum (Extensible)** added to `wrestler.py`: `HEAVY_HITTER`, `GRAPPLER`, `HIGH_FLYER`, `BRAWLER`, `SHOWMAN`, `DIRTY_TRICKS`, `MEAN_STREAK`. Add `style: Optional[WrestlerStyle] = None` to `Wrestler`. `None` = unclassified rookie, assigned on generation. | Verify `WrestlerStyle.HIGH_FLYER` serializes to `"HIGH_FLYER"`. Verify existing tests are unaffected (default `None`). |
| *DLR-11.5.1* | *FR-11.5.0* | **`talent_generator.py` — `generate_class(dojo)`**: Generates 1-3 rookies. `class_size = random.randint(1, 3)`. For each rookie: (a) roll style via style_roll logic, (b) compute stat baselines, (c) construct a `Wrestler` object. Return `List[Wrestler]`. | Verify a LUCHA Dojo with scouting=100 produces at least one HIGH_FLYER over 10 calls. |
| *DLR-11.5.2* | *FR-11.5.0* | **Style Roll Logic**: `p = random.random()`. If `p < 0.80`: assign the `WrestlerStyle` that maps to the `DojoStyle` (see Style Map Table). Else: assign a random `WrestlerStyle`. | Verify ~80% of graduates match dojo style in a 1000-run Monte Carlo. |
| *DLR-11.5.3* | *FR-11.5.0* | **Stat Baseline Formula**: `base = random.randint(30, 50) + int(dojo.manager.scouting_skill * 0.2)`. Each stat is independently rolled. Stats are clamped to `[0, 100]`. | Verify scouting=100 yields rookies with stats between 50-70. Verify scouting=0 yields 30-50. |
| *DLR-11.5.4* | *FR-11.5.0* | **Style Bias Table**: Applied as a flat bonus (+15) to specific stats during generation, biasing the stat towards the Dojo's specialty (see Style Bias Table below). | Verify STRONG_STYLE graduates have higher average Strength than LUCHA graduates over 50 trials. |
| *DLR-11.6.1* | *FR-11.6.0* | **`dojo_engine.py` — `process_weekly_training(dojo)`**: For each student in `dojo.students`: compute `stat_increase = (dojo.manager.training_skill * 0.1) + (dojo.equipment_level * 0.05)`. Apply `int(round(stat_increase))` to the style-targeted stats. Clamp all stats to 100. | Verify training_skill=100, equipment_level=5 yields a +11 stat gain per turn. |
| *DLR-11.6.2* | *FR-11.6.0* | **Training Target Stats**: The stats boosted weekly are driven by the Dojo's style (see Style Bias Table). Only listed stats receive the bonus. | Verify TECHNICAL Dojo grows `work_rate` and `intelligence`, not `agility`. |
| *DLR-11.7.1* | *FR-11.7.0* | **`dojo_engine.py` — `award_graduate_xp(dojo, event_type)`**: `event_type` is `"MATCH_WIN"` (+5 XP) or `"TITLE_WIN"` (+50 XP). After each XP award, check `dojo.xp >= dojo.prestige_stars * 500 + 500`. If true: increment `prestige_stars` (max 5). | Verify 100 match wins (500 XP) triggers a star promotion. Verify star capped at 5. |
| *DLR-11.8.1* | *FR-11.8.0* | **`dojo_engine.py` — `check_capacity(dojo)`**: `max_capacity = (dojo.prestige_stars * 2) + dojo.equipment_level`. Return `len(dojo.students) < max_capacity`. | Verify 1-star, equipment=1 Dojo has capacity 3. Verify 5-star, equipment=5 Dojo has capacity 15. |
| *DLR-11.9.1* | *FR-11.9.0* | **`financial_engine.py`**: Sum maintenance costs across all `company.dojos`. `dojo_cost = sum((d.equipment_level * 1000) + (d.prestige_stars * 500) for d in company.dojos)`. Add to `total_expenses`. | Verify a 3-star, Level-4 equipment Dojo costs $5,500/week. Verify 0 Dojos = $0 additional expense. |
| *DLR-11.9.2* | *FR-11.9.0* | **`generate_class` Turn Gate**: `talent_generator.generate_class()` is only called when `game_turn % 4 == 0`. The caller (main game loop) is responsible for this check; the generator itself has no state. | Verify class is generated on turn 4, 8, 12. Verify it is NOT generated on turn 3. |
| *DLR-11.10.1* | *FR-11.10.0* | **`company.py`**: Add `dojos: List[Dojo] = Field(default_factory=list)`. No hard capacity limit on number of Dojos. Maintenance scales automatically. | Verify `Company` with 3 Dojos totals the maintenance of all 3. |

---

## Style Map & Bias Tables

### DojoStyle → WrestlerStyle Mapping (80% probability)

| DojoStyle | WrestlerStyle |
| :--- | :--- |
| `STRONG_STYLE` | `HEAVY_HITTER` |
| `TECHNICAL` | `GRAPPLER` |
| `LUCHA` | `HIGH_FLYER` |
| `BRAWLER` | `BRAWLER` |
| `SHOWMAN` | `SHOWMAN` |

### Style Bias Table (Stat Bonuses at Generation — flat +15)

| DojoStyle | Primary Stat Bonus | Secondary Stat Bonus |
| :--- | :--- | :--- |
| `STRONG_STYLE` | `in_ring.strength` | `in_ring.stamina` |
| `TECHNICAL` | `psychology.work_rate` | `psychology.intelligence` |
| `LUCHA` | `in_ring.agility` | `psychology.selling` |
| `BRAWLER` | `in_ring.strength` | `backstage.ego` |
| `SHOWMAN` | `psychology.selling` | `popularity.heat` |

### Style Bias Table (Training Focus — weekly bonus applied to)

| DojoStyle | Training Targets |
| :--- | :--- |
| `STRONG_STYLE` | `in_ring.strength`, `in_ring.stamina` |
| `TECHNICAL` | `psychology.work_rate`, `psychology.intelligence` |
| `LUCHA` | `in_ring.agility`, `psychology.selling` |
| `BRAWLER` | `in_ring.strength`, `backstage.ego` |
| `SHOWMAN` | `psychology.selling`, `in_ring.agility` |

---

## Technical Specs & Architecture

### New Files

#### `src/models/promotion/dojo.py`
```python
# Psuedo-code for field layout only
class DojoStyle(str, Enum): STRONG_STYLE, TECHNICAL, LUCHA, BRAWLER, SHOWMAN

class DojoManager(BaseModel): name, scouting_skill, training_skill

class Dojo(BaseModel): id, name, style, prestige_stars, equipment_level, appeal, xp, manager, students, graduates
```

#### `src/engine/talent_generator.py`
- `STYLE_MAP: Dict[DojoStyle, WrestlerStyle]` — mapping table.
- `STYLE_BIAS: Dict[DojoStyle, List[str]]` — lists of stat path strings for generation bias.
- `generate_class(dojo: Dojo) -> List[Wrestler]` — the public entry point.
- `_roll_style(dojo_style: DojoStyle) -> WrestlerStyle` — internal style roll.
- `_generate_rookie(dojo: Dojo) -> Wrestler` — builds one `Wrestler` object.

#### `src/engine/dojo_engine.py`
- `process_weekly_training(dojo: Dojo)` — applies training bonuses.
- `award_graduate_xp(dojo: Dojo, event_type: str)` — awards XP and checks star threshold.
- `check_capacity(dojo: Dojo) -> bool` — capacity gate for enrollment.

### Modified Files

- **`src/models/wrestler/wrestler.py`**: Add `WrestlerStyle` enum and `style: Optional[WrestlerStyle] = None` field.
- **`src/models/promotion/company.py`**: Add `dojos: List[Dojo] = Field(default_factory=list)`.
- **`src/engine/financial_engine.py`**: Sum dojo maintenance into `total_expenses`.

---

## Work Order Refinement

- **To The Booker**:
  - Build `dojo.py`, `talent_generator.py`, and `dojo_engine.py` in that order (models first, then logic).
  - `WrestlerStyle` must be added to `wrestler.py` before other files import it.
  - The stat paths in `STYLE_BIAS` should be stored as `(model_name, stat_name)` tuples so the engine can use `getattr` safely.
  - The `generate_class` function should return fully-valid `Wrestler` Pydantic objects — do not return partial dicts.

- **To The Money Man**:
  - The Dojo maintenance in `financial_engine.py` must iterate `company.dojos` — if the list is empty, the expense is $0.
  - The `Dojo.graduates` list holds `UUID`s matching wrestler IDs on the main roster. This is the cross-reference for `award_graduate_xp`.

---

## Referee Handbook (QA Scenarios)

- **Positive**: LUCHA Dojo generates a HIGH_FLYER rookie with boosted Agility.
- **Positive**: Training_skill=100, equipment=5 gives +11 weekly stat growth on targeted stats.
- **Positive**: 100 match wins triggers a prestige star promotion.
- **Positive**: 3 Dojos totals maintenance costs correctly.
- **Negative**: Student cannot be added if Dojo is at capacity.
- **Negative**: `prestige_stars` cannot exceed 5 even with unlimited XP.
- **Edge Case**: A Dojo with 0 students processes training with no errors.
- **Edge Case**: A Showman Dojo in turn 4 generates 1-3 rookies with `SHOWMAN` style ~80% of the time.
