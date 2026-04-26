# Crowd Mechanics & Fluid KayfabeStatus - Detailed Logic Requirements (DLR)

## Traceability Table

| DLR ID | Linked HLR ID | Technical Requirement Explanation | Confirmation Test Case |
| :--- | :--- | :--- | :--- |
| *DLR-4.1.1* | *FR-4.1.0* | Remove `KayfabeStatus` enum field from `Wrestler` model initialization. Add dynamic `@property` `kayfabe_status` returning an `KayfabeStatus` Enum. | Verify `wrestler.kayfabe_status` calculates dynamically based on `popularity`. |
| *DLR-4.2.1* | *FR-4.2.0* | Implement `apply_opposing_metric_decay()` logic in `match_simulator.py`. `Decay_Multiplier = (Professionalism + (100 - Ego)) / 200`. (Min 0.2, Max 1.5). If `pop_gain > 0`, `heat_delta -= (pop_gain * Decay_Multiplier)`. High prof / low ego = high decay (pure babyface loses Heat fast). High ego / low prof = low decay (anti-hero holds both). | Verify a pure babyface loses MORE Heat when gaining Pop than an anti-hero. |
| *DLR-4.3.1* | *FR-4.3.0* | In `Wrestler.kayfabe_status` property: `margin = abs(pop - heat)`. `if margin <= 20 and hype >= 70: return KayfabeStatus.TWEENER`. `elif pop >= heat: return KayfabeStatus.FACE`. `else: return KayfabeStatus.HEEL`. | Verify 90 Pop / 80 Heat / 90 Hype evaluates as `TWEENER`. |
| *DLR-4.4.1* | *FR-4.4.0* | `Hype` delta is decoupled from KayfabeStatus. `Base Shift` applies directly to `Hype_Delta`. If `Base Shift > 0`, the winner gains `Pop` if Face, `Heat` if Heel. If `TWEENER`, gains both divided by 2. | Verify Hype grows passively on 4-star matches. |

## Technical Specs & Architecture

- **Affected Files**:
  - `src/models/wrestler/wrestler.py` [MODIFY]
  - `src/engine/match_simulator.py` [MODIFY]

- **Data Structures**:
  - `wrestler.py`:
    - Remove `kayfabe_status: KayfabeStatus = KayfabeStatus.TWEENER` from fields.
    - Add `@property def kayfabe_status(self) -> KayfabeStatus`

- **Logic Flow**: 
  1. Post-match, simulator determines the `Base Shift` (Star Rating - 2.5 * 4).
  2. `Hype Delta` = `Base Shift`.
  3. Depending on dynamic kayfabe_status, winner gets Pop/Heat.
  4. Opposing Metric Decay is applied: Gaining Pop reduces Heat by `Pop_Delta * Decay_Multiplier`.
  5. Apply Deltas to `wrestler.popularity`.

## Referee Handbook (QA Scenarios)

- **Positive Tests**:
  - `test_dynamic_alignment`: Instantiate a wrestler with 50 Pop, 50 Heat. Assert kayfabe_status is `FACE` (pop>=heat). Set Hype to 80, Pop 80, Heat 70. Assert kayfabe_status is `TWEENER`. Set Heat to 100, Pop to 20. Assert `HEEL`.
  - `test_opposing_metric_decay`: Run a post-match calculation. Assert gaining 10 Pop reduces Heat by a calculated amount based on ego/professionalism.
