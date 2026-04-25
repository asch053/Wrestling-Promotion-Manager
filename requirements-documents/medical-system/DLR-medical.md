# Injury, Fatigue, and Medical Recovery - Detailed Logic Requirements (DLR)

## Traceability Table

| DLR ID | Linked HLR ID | Technical Requirement Explanation | Confirmation Test Case |
| :--- | :--- | :--- | :--- |
| *DLR-10.1.1* | *FR-10.1.0* | Add `fatigue: int = 0` (0-100) and `injury_status: Optional[Injury] = None` to `Wrestler` model. | Verify defaults on instantiation. |
| *DLR-10.2.1* | *FR-10.2.0* | **Fatigue Gain**: `gain = (spots_count * 2) * match_type_multiplier`. Multipliers: Standard=1.0, Tag=0.8, Hardcore=1.5, Cage=2.0. | Verify 10-spot Cage match = 40 fatigue gain. |
| *DLR-10.3.1* | *FR-10.3.0* | **Injury Probability**: During `simulate_match`, roll for injury once per participant. $P = 0.02 \times (1.0 + Fatigue/100) \times (1.0 - Agility/200)$. | Verify 0 fatigue/100 agility = 1% base rate. Verify 100 fatigue/0 agility = 4% rate. |
| *DLR-10.4.1* | *FR-10.4.0* | **Injury Selection**: If injury roll hits, select from `injury_lookup_table` based on `severity` roll (70% Minor, 30% Major). | Verify distribution over 100 trials. |
| *DLR-10.5.1* | *FR-10.5.0* | **Medical Staff**: Add `medical_staff_level: int = 1` (1-5) to `Company`. | Verify default level 1. |
| *DLR-10.5.2* | *FR-10.5.0* | **Financial Expense**: In `financial_engine.py`, add `medical_expense = staff_level * 2000`. | Verify Level 3 = $6,000 expense. |
| *DLR-10.6.1* | *FR-10.6.0* | **Weekly Recovery**: `recovery_boost = 1.0 + (staff_level * 0.2)`. `fatigue = max(0, fatigue - (10 * recovery_boost))`. `injury_weeks -= (1 * recovery_boost)`. | Verify Level 5 (2.0x) recovers 20 fatigue and 2 weeks of injury time per turn. |
| *DLR-10.7.1* | *FR-10.7.0* | **Morale Impact**: Sidelined wrestlers suffer `-10` morale immediately. | Verify morale drop on Major injury. |

## Injury Lookup Table

| Injury Name | Type | Duration (Weeks) | Stat Penalty |
| :--- | :--- | :--- | :--- |
| **Sprained Ankle** | Minor | 1 - 2 | -20% Agility |
| **Bruised Ribs** | Minor | 1 - 3 | -20% Stamina |
| **Strained Back** | Minor | 2 - 4 | -20% Strength |
| **Concussion** | Minor | 2 - 4 | -20% Psychology |
| **Broken Arm** | Major | 4 - 8 | Sidelined |
| **Torn ACL** | Major | 12 - 24 | Sidelined |
| **Neck Injury** | Major | 8 - 16 | Sidelined |
| **Separated Shoulder**| Major | 6 - 12 | Sidelined |

## Technical Specs & Architecture

- **Affected Files**:
  - `src/models/wrestler/wrestler.py` [MODIFY]: Add `fatigue`, `injury_weeks_remaining`, `is_sidelined`.
  - `src/models/promotion/company.py` [MODIFY]: Add `medical_staff_level`.
  - `src/engine/match_simulator.py` [MODIFY]: Add fatigue gain and injury check loop.
  - `src/engine/financial_engine.py` [MODIFY]: Add medical staff weekly expense.
  - `src/engine/medical_engine.py` [NEW]: Weekly processing of fatigue and injury healing.

- **Injury Logic**:
  ```python
  def calculate_injury_chance(wrestler):
      base_rate = 0.02
      fatigue_factor = 1.0 + (wrestler.fatigue / 100.0)
      agility_factor = 1.0 - (wrestler.in_ring.agility / 200.0)
      return base_rate * fatigue_factor * agility_factor
  ```

- **Stat Penalty Logic**:
  Minor injuries apply a multiplier to the base stat.
  `effective_agility = base_agility * 0.8` if `injury_type == MINOR`.

- **Sidelined Logic**:
  `can_book(wrestler)` returns `False` if `wrestler.is_sidelined`.

## Work Order Refinement

- **To The Booker**:
  - Implement `medical_engine.py` first. This will be called at the end of every event processing loop.
  - Ensure `match_simulator.py` updates the `Wrestler` objects directly (or returns the status in `MatchReport` for the caller to apply).
  
- **To The Referee**:
  - Test the probability formula across the full range of Fatigue and Agility.
  - Verify that Sidelined wrestlers cannot be booked in the `BookingSheet` validator.
  - Verify that Medical Staff Level 5 significantly shortens recovery time for a Torn ACL.
