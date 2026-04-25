# Backstage Politics & Locker Room Morale - Executive Summary

The locker room is as dangerous as the ring. Egos clash, grudges fester, and a disgruntled star can sabotage an entire promotion. This feature introduces a persistent `morale` stat for every wrestler, a dynamic Morale Shift algorithm, and a volatile Backstage Incident generator that can override the Booker's carefully planned cards.

## High-Level Requirements (HLR) Document

**Feature ID**: F-008
**Feature Name**: Backstage Politics & Locker Room Morale
**Description**: Every wrestler tracks a `morale` stat (0-100) that fluctuates based on booking success, storyline status, financial fairness, and backstage relationships. When morale is low and ego is high, wrestlers can trigger "Backstage Incidents" that sabotage the show, poison their faction, or damage the company's public image. Morale also acts as a multiplier on in-ring Work Rate and a negotiation weight for contract re-signing.

**User Stories**:
- As a Booker, I need to track the morale of every wrestler on my roster. Winning builds confidence; losing breaks it—especially for big egos.
- As a Booker, I want wrestlers on a `PUSH_STAR` storyline to receive a morale boost, while wrestlers not booked on the card ("Benched") suffer morale decay.
- As the Money Man, I want a wrestler's morale to drop if they discover a lower-Hype peer is earning more money than them (Financial Fairness).
- As a Booker, I need to fear that a high-Ego, low-Professionalism, low-Morale wrestler might "Refuse to Lose"—forcing me to change my `designated_winner` mid-show.
- As a Booker, I need to worry that a toxic wrestler can become a "Locker Room Poison", dragging down the morale of everyone in their Faction.
- As the Money Man, I want a wrestler with dangerously low morale to be harder to re-sign when their contract expires.
- As a Referee (Match Engine), I want `morale` to act as a multiplier on `Work Rate`. A 100-morale wrestler performs at full potential; a 20-morale wrestler sandbags.

**Functional Requirements**:
- **FR-8.1.0 - Morale Stat**: Add `morale: int = 50` to the `Wrestler` model.
- **FR-8.2.0 - Weekly Morale Shift Algorithm**: Create `calculate_morale_shift(wrestler, event, company)` that adjusts morale at the end of each show based on:
  - **Booking Result**: Won = `+5`. Lost = `-3`. Not booked = `-5`.
  - **Ego Amplifier**: High-ego wrestlers suffer **double** the negative morale shift from losses.
  - **Storyline Boost**: Being the `target_wrestler` of an active `PUSH_STAR` storyline = `+10`.
  - **Financial Fairness**: If any roster peer with lower Hype earns a higher `weekly_salary`, apply `-10` penalty.
- **FR-8.3.0 - Backstage Incident Generator**: Create `generate_incidents(company)` that evaluates each wrestler. If `ego > 70 AND professionalism < 40 AND morale < 30`, roll for an incident:
  - **Refusal to Lose** (30% chance): The wrestler overrides the `designated_winner` on their next match. They become the winner regardless of the booking.
  - **Locker Room Poison** (40% chance): Every member of the wrestler's Faction loses `-15` morale.
  - **Public Shooting** (30% chance): The wrestler publicly criticizes the company. Company Hype drops by `5`.
- **FR-8.4.0 - In-Ring Morale Modifier**: In `match_simulator.py`, the effective `work_rate` used for Star Rating calculation is: `effective_work_rate = work_rate * (morale / 100)`. A wrestler at 20 morale only performs at 20% of their potential.
- **FR-8.5.0 - Contract Negotiation Weight**: When calculating re-sign difficulty, `morale` acts as a modifier. Low morale = higher chance of refusing to re-sign or demanding more money.

**Acceptance Criteria**:
- A wrestler who loses 5 matches in a row with 100 Ego has their morale tank to near-zero.
- A wrestler with 90 Ego, 10 Professionalism, and 15 Morale has a chance to trigger a "Refusal to Lose" incident.
- A wrestler at 20 morale performing in a match generates a significantly lower Star Rating than the same wrestler at 100 morale.
- A wrestler underpaid relative to a lower-Hype peer automatically loses morale.

## Logic Blueprint

- **Weekly Morale Shift**:
  - `Base Shift = +5 (Win) / -3 (Loss) / -5 (Benched)`
  - `Ego Penalty = Base Shift * (1 + ego / 100)` if Base Shift is negative
  - `Storyline Boost = +10` if target of PUSH_STAR
  - `Fairness Penalty = -10` if underpaid relative to lower-hype peer
  - `Final = clamp(morale + sum_of_all_shifts, 0, 100)`
- **Incident Trigger**: `ego > 70 AND professionalism < 40 AND morale < 30`
- **In-Ring Modifier**: `effective_work_rate = work_rate * (morale / 100)`

## File Impact List

- `[MODIFY]` `src/models/wrestler/wrestler.py`
- `[MODIFY]` `src/engine/match_simulator.py`
- `[NEW]` `src/engine/morale_engine.py`
- `[NEW]` `src/engine/incident_generator.py`

## Agent Assignments

- **To Road Agent**: Draft the DLR. Define the exact math for `calculate_morale_shift()`, the incident probability table, and the `Refusal to Lose` override logic.
- **To The Booker**: *(Future Step)* Build `morale_engine.py` and `incident_generator.py`. Update `match_simulator.py` with the morale Work Rate modifier.
- **To The Referee**: *(Future Step)* Write tests proving morale shifts, incident triggers, and the Work Rate multiplier.
