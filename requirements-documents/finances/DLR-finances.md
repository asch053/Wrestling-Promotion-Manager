# Company Management & Finances - Detailed Logic Requirements (DLR)

## Traceability Table

| DLR ID | Linked HLR ID | Technical Requirement Explanation | Confirmation Test Case |
| :--- | :--- | :--- | :--- |
| *DLR-5.1.1* | *FR-5.1.0* | Implement `Company` model tracking `bank_balance`, `current_roster: List[Wrestler]`, `past_roster: List[Wrestler]`. Track `past_events: List[Event]`. | Verify instantiation and roster arrays. |
| *DLR-5.1.2* | *FR-5.1.0* | Implement `calculate_current_hype()` and `calculate_current_excitement()` methods on `Company`. Decay factor = `0.8` per 'turn' looking backwards. | Assert calculation logic correctly applies decay mathematically. |
| *DLR-5.2.1* | *FR-5.2.0* | Implement `Contract` Pydantic model with `appearance_fee: int`, `weekly_salary: int`, `merch_cut_percentage: float`. Add optional `contract` to `Wrestler`. | Verify successful instantiation of a Wrestler with a Contract. |
| *DLR-5.3.1* | *FR-5.3.0* | Implement `EventScale` Enum (HOUSE_SHOW, TV_TAPING, PPV, MEGA_EVENT). Implement `Event` model containing scale, location, and financial totals. | Verify instantiation of Event. |
| *DLR-5.4.1* | *FR-5.4.0* | `financial_engine.py`: Base Gate = `(Company Hype * 10) + (Company Excitement * 20)`. Scale multipliers: HS(1x), TV(2x), PPV(5x), MEGA(10x). Staleness penalty = `0.8` if location == prev_location. | Assert expected gate revenue based on specific injected stats. |
| *DLR-5.4.2* | *FR-5.4.0* | **Merch Revenue (Fluid KayfabeStatus Aware)**: Iterate roster. Use `wrestler.kayfabe_status` (dynamic property). If `FACE` or `HEEL`: `w_merch = hype * 50` (high loyalty peak). If `TWEENER`: `w_merch = min(hype * 60, 4000)` (broader appeal, lower loyalty cap). Add `w_merch` to total. Add `w_merch * merch_cut_percentage` to `talent_merch_cut`. | Verify Tweener at 50 Hype generates 3000 merch (50*60) vs Face at 50 Hype generating 2500 (50*50). Verify Tweener at 100 Hype caps at 4000 vs Face at 100 Hype generating 5000. |
| *DLR-5.5.1* | *FR-5.5.0* | Expenses: `Talent` = sum(fees). `Staging` = Scale (HS=$5k, TV=$15k, PPV=$50k, MEGA=$200k). `Travel` = 0 if same location, else $10k. `Overheads` = $5k + (len(past_events) * $100). | Assert expected expenses based on specific injected parameters. |
| *DLR-5.6.1* | *FR-5.6.0* | The engine creates a `FinancialReport` and explicitly adds `net_profit` to `Company.bank_balance`. | Verify company bank balance changes by exactly `net_profit`. |

## Technical Specs & Architecture

- **Affected Files**:
  - `src/models/wrestler/contract.py` [NEW]
  - `src/models/wrestler/wrestler.py` [MODIFY]
  - `src/models/promotion/event.py` [NEW]
  - `src/models/promotion/company.py` [NEW]
  - `src/engine/models/financial_report.py` [NEW]
  - `src/engine/financial_engine.py` [NEW]

- **Data Structures**:
  - `contract.py`:
    - `class Contract(BaseModel)`
  - `event.py`:
    - `class EventScale(str, Enum)`
    - `class Event(BaseModel)`: `name: str`, `location: str`, `scale: EventScale`, `match_reports: List[MatchReport]`
  - `company.py`:
    - `class Company(BaseModel)`: Properties for `current_hype` and `current_excitement`.
  - `financial_report.py`:
    - `class FinancialReport(BaseModel)`: Explicit dicts for `revenue_breakdown` and `expense_breakdown`.

- **Logic Flow** (`financial_engine.py` -> `process_event_finances(company: Company, event: Event)`): 
  1. **Calculate Merch**: For each wrestler, check `wrestler.kayfabe_status` (dynamic property). Apply kayfabe_status-specific multiplier and cap. Deduct `Merch * merch_cut_percentage` as the talent's cut.
  2. **Calculate Gate**: Determine Company Hype and Excitement. Apply `EventScale` multiplier. Check `Company.past_events[-1].location` for Staleness.
  3. **Calculate Expenses**: Sum Staging Base, Travel (if location changed), Overheads, and total Talent Cost (appearance fees + merch cuts).
  4. **Finalize**: Calculate Net Profit. Update `Company.bank_balance`. Append `Event` to `Company.past_events`. Return the `FinancialReport`.

## Work Order Refinement

- **To The Booker**: 
  - The decaying algorithm in `Company` needs to loop backwards. E.g., `decay = 1.0`, `for item in reversed(list): decay *= 0.8; total += item.value * decay`.
  - Pydantic models might need `@computed_field` or properties for the dynamic calculations.
  - **IMPORTANT**: The merch calculation must call `wrestler.kayfabe_status` which is now a dynamic `@property` based on Pop/Heat balance, not a stored field. This means merch revenue can shift event-to-event as wrestlers organically turn.
- **To The Money Man**: 
  - The `bank_balance` should never drop below zero without triggering some sort of "Bankruptcy" flag in the future, but for this sprint, allowing negative balances is fine.

## Referee Handbook (QA Scenarios)

- **Positive Tests**:
  - `test_company_decay_math`: Create a company with 3 past events. Verify the `current_excitement` aggregates cleanly with the 0.8 decay factor.
  - `test_financial_engine_profit`: Run a House Show that is highly profitable. Assert `company.bank_balance` increases.
- **Strategic Edge Case Tests**:
  - `test_staleness_penalty_and_travel`: Run two identical events in the exact same location. Assert the second event generates exactly 20% less gate revenue and travel cost drops to $0.
  - `test_merch_commission`: Verify that a highly hyped wrestler with a 50% merch cut generates a massive expense item for the company compared to a wrestler with a 5% cut.
  - `test_tweener_merch_economics`: Verify a Tweener (Pop ≈ Heat, high Hype) generates merch using the `hype * 60` formula but is capped at 4000. Verify a pure Face with the same Hype generates more at 100 Hype but less at 50 Hype.
