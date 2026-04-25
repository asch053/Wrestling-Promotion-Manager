# Promotion Manager (Company) & Finances - Executive Summary

A successful wrestling promotion isn't just about drawing money—it's about managing a living, breathing Company. This feature introduces the overarching `Company` object to track the promotion's overall bank balance, roster, and momentum, along with the Financial Engine to calculate net profit on a per-event basis. 

## High-Level Requirements (HLR) Document

**Feature ID**: F-005
**Feature Name**: Company Management & Financial Engine
**Description**: Implement a `Company` object to act as the root state for the game. It tracks the roster, finances, and overarching hype/excitement. The Financial Engine calculates event `net_profit` (Revenue - Expenses) and updates the Company's bank balance.

**User Stories**:
- As a Booker, I want a `Company` object that tracks my total bank balance, current roster, and alumni (past roster).
- As a Booker, I want the overall company's "Hype" to be the sum of my current roster's hype, plus a decaying lingering hype from legends who used to work here.
- As a Booker, I want the company's "Excitement" to aggregate the momentum of my last event plus the decaying momentum of previous historical events.
- As the Money Man, I need to sign wrestlers to Contracts specifying their event fees, weekly salaries, and merch cuts.
- As the Money Man, I want to calculate the cost of staging an event based on its scale and travel costs.
- As a Booker, I must balance travel costs against "location staleness." If I run 10 shows in the same arena, the local crowd gets bored and gate sales drop.

**Functional Requirements**:
- **FR-5.1.0 - Company Object**: Define `Company` with `name`, `bank_balance`, `current_roster`, `past_roster`. It must calculate `current_hype` (sum of current roster + decaying past roster hype) and `current_excitement` (last event + decaying past events).
- **FR-5.2.0 - Wrestler Contracts**: Add a `Contract` model to `Wrestler` with `appearance_fee`, `weekly_salary`, and `merch_cut_percentage`.
- **FR-5.3.0 - Event State & Staleness**: Define an `Event` model containing `event_scale` and `location`. If `location` equals the previous `location`, a staleness penalty hits Gate Sales.
- **FR-5.4.0 - Revenue Calculation**: 
  - Gate Sales: Based on Company's `current_hype`, `current_excitement`, `event_scale`, and Location Staleness.
  - TV Deals: Based on Company's `current_hype`.
  - Merchandise: Calculated individually per wrestler based on their `hype` and dynamic `Alignment`. `Faces` and `Heels` have high loyalty peaks (higher max sales). `Tweeners` appeal to a broader audience, selling more diverse gear (higher base multiplier) but have a lower loyalty peak cap.
- **FR-5.5.0 - Expense Calculation**:
  - Talent Costs: Sum of `appearance_fee` + (`Merch Revenue` * `merch_cut_percentage`).
  - Staging Costs: Exponentially higher for larger `event_scale`.
  - Travel Costs: High if `location` changes, 0 if location is the same.
  - Overheads: `fixed_overhead` + `non_fixed_overhead`.
- **FR-5.6.0 - Financial Report**: Output a `FinancialReport` that itemizes the event's P&L and updates the `Company.bank_balance`.

**Acceptance Criteria**:
- A massively scaled event with high travel costs and expensive talent results in a net *loss* to the Company's bank balance if hype isn't high enough.
- Moving a highly hyped wrestler to the `past_roster` causes an immediate drop in `current_hype`, but provides a slow decay rather than a total loss of momentum.

## Logic Blueprint

- **Company State**:
  - `Company.current_hype` = `Sum(Current_Roster.hype) + Sum(Past_Roster.hype * decay_factor)`
  - `Company.current_excitement` = `Last_Event.excitement + Sum(Historical_Events.excitement * decay_factor)`
- **Revenue**:
  - `Gate` = `(Company Hype * X) + (Company Excitement * Y) * ScaleMultiplier * StalenessPenalty`
- **Expenses**:
  - `Talent` = `Sum(appearance_fee) + Sum(merch_revenue * merch_cut)`
  - `Travel` = `Cost` if `location != prev_location` else `0`

## File Impact List

- `[NEW]` `src/models/promotion/company.py`
- `[NEW]` `src/models/wrestler/contract.py`
- `[MODIFY]` `src/models/wrestler/wrestler.py`
- `[NEW]` `src/models/promotion/event.py`
- `[NEW]` `src/engine/models/financial_report.py`
- `[NEW]` `src/engine/financial_engine.py`

## Agent Assignments

- **To Road Agent**: Draft the DLR. Define the Pydantic schemas for `Company` and how the decay functions work for `current_hype` and `current_excitement`. Define the economic multipliers for the Financial Engine.
- **To The Booker**: *(Future Step)* Write the calculation logic in `financial_engine.py` to update the Company object.
- **To The Referee**: *(Future Step)* Write tests proving the Company's bank balance correctly shifts after a financial report is processed.
