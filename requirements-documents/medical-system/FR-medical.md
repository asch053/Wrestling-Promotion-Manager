# Injury, Fatigue, and Medical Recovery - Executive Summary

Wrestling is a physical toll. Every bump has a cost, and every main eventer has a breaking point. This feature introduces a persistent `fatigue` stat, a dynamic Injury Engine that can sideline stars, and a Medical Staff system that allows players to manage the integrity of their roster. "Workhorse" booking now carries the risk of career-altering injuries.

## High-Level Requirements (HLR) Document

**Feature ID**: F-010
**Feature Name**: Injury, Fatigue, and Medical Recovery
**Description**: Wrestlers track `fatigue` (0-100) which accumulates based on match intensity and duration. High fatigue degrades performance and spikes injury risk. Injuries can be Minor (stat penalties) or Major (sidelined). Players hire Medical Staff to accelerate recovery and reduce long-term selling_burden.

**User Stories**:
- As a Booker, I need to monitor the `fatigue` of my wrestlers. Constant main-eventing should wear them down.
- As a Booker, I want to see the risk of injury increase if I book a wrestler who is already fatigued.
- As a Booker, I want certain match types (e.g., Hardcore, Cage) to cause more fatigue and carry higher base injury risks.
- As a Money Man, I want to hire a Medical Staff (Levels 1-5) to help my stars recover faster, knowing it adds to my weekly expenses.
- As a Booker, I want to know if a wrestler is Sidelined (Major Injury) or just hampered by a Minor Injury (active but penalized).
- As a Wrestler, I want my morale to drop if I suffer a Major Injury that keeps me out of the ring.
- As a Referee, I want to calculate injury checks during the match simulation based on spots and fatigue levels.

**Functional Requirements**:
- **FR-10.1.0 - Fatigue Stat**: Add `fatigue: int = 0` (0-100) to the `Wrestler` model.
- **FR-10.2.0 - Fatigue Accumulation**: After a match, wrestlers gain fatigue: `fatigue_gain = (spots_count * 2) * match_type_multiplier`.
- **FR-10.3.0 - Injury Engine**: Implement an `InjuryCheck` in the simulator. 
  - **Probability Formula**: $P(Injury) = Base\_Rate \times (1.0 + \frac{Fatigue}{100}) \times (1.0 - \frac{Agility}{200})$.
- **FR-10.4.0 - Minor vs. Major Injuries**:
  - **Minor**: -20% penalty to all physical stats (Strength, Agility, Stamina) for $X$ weeks. Wrestler remains bookable.
  - **Major**: Sidelined (not bookable) for $Y$ weeks.
- **FR-10.5.0 - Medical Staff System**: 
  - `Company` model stores `medical_staff_level: int = 1` (1-5).
  - Level 1: $1,000/week. Level 5: $10,000/week.
  - Recovery multiplier: `recovery_boost = 1.0 + (staff_level * 0.2)`.
- **FR-10.6.0 - Weekly Recovery Logic**: Every game-turn, wrestlers recover fatigue and injury time:
  - `fatigue_recovery = base_rate (e.g., 10) * recovery_boost`.
  - `injury_time_remaining -= 1 * recovery_boost`.
- **FR-10.7.0 - Morale Integration**: Sidelined wrestlers suffer `-10` morale upon injury.
- **FR-10.8.0 - Financial Integration**: Medical staff salaries are a fixed weekly expense in `financial_engine.py`.

**Acceptance Criteria**:
- A wrestler with 80 fatigue is significantly more likely to get injured than one with 0 fatigue.
- A high-level Medical Staff reduces the time a star is sidelined compared to a base-level staff.
- Sidelined wrestlers cannot be added to a `BookingSheet`.
- Minor injuries show up as stat debuffs in the wrestler profile.

## Logic Blueprint

- **Injury Probability**: $Base\_Rate \times (1.0 + Fatigue/100) \times (1.0 - Agility/200)$
- **Fatigue Recovery**: $10 \times (1.0 + (Staff\_Level \times 0.2))$
- **Medical Expense**: $Staff\_Level \times 2000$ (adjusted from story for balance: $2000, $4000, etc.)

## File Impact List

- `[MODIFY]` `src/models/wrestler/wrestler.py`
- `[MODIFY]` `src/models/promotion/company.py`
- `[MODIFY]` `src/engine/match_simulator.py`
- `[MODIFY]` `src/engine/financial_engine.py`
- `[MODIFY]` `src/engine/morale_engine.py`
- `[NEW]` `src/engine/medical_engine.py`

## Agent Assignments

- **To Road Agent**: Draft the DLR. Design the `injury_lookup_table` (listing types of injuries, their durations, and whether they are Minor or Major).
- **To The Booker**: *(Future Step)* Build `medical_engine.py`. Update `match_simulator.py` with the InjuryCheck loop.
- **To The Referee**: *(Future Step)* Write tests for fatigue accumulation and recovery.
