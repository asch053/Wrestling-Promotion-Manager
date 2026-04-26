# Crowd Mechanics & Dynamic Match Engine - Executive Summary

The Crowd is the third participant in any wrestling match. This feature introduces a dynamic `Crowd` state that reacts to the in-ring action. It also introduces persistent, fluid wrestler popularity tracking (Hype, Pop, Heat) and a dynamic KayfabeStatus system driven by the "Psychology of the Crowd".

## High-Level Requirements (HLR) Document

**Feature ID**: F-004
**Feature Name**: Crowd Mechanics & Fluid KayfabeStatus
**Description**: Implement a persistent Crowd state during matches. Track persistent wrestler popularity where `Hype` is a macro-metric of overall volume/star-power, while `Pop` (Face reaction) and `Heat` (Heel reaction) exist in a fluid balance. Gaining one decays the other. `KayfabeStatus` (Face/Heel/Tweener) is no longer a static choice, but a dynamic state derived from this balance.

**User Stories**:
- As a Fan, I want the crowd to get hyped during big spots and go quiet if the match is boring.
- As a Booker, I want my wrestlers' `Hype` to represent their overall star power, growing naturally through high-quality matches regardless of their storyline.
- As a Booker, I want `Pop` and `Heat` to be fluid. If my top Face starts doing dirty heel tactics to win, they should gain Heat, which actively decays their Pop.
- As a Booker, I want a wrestler's personality to affect this decay. A "Pure Babyface" should lose Heat very quickly, while a "Gritty Underdog" or "Anti-Hero" can maintain a more balanced mix of Pop and Heat.
- As a Booker, I want a wrestler's KayfabeStatus to automatically shift to `TWEENER` if they have high Hype but the crowd is split evenly between cheering (Pop) and booing (Heat).

**Functional Requirements**:
- **FR-4.1.0 - Fluid Popularity Model**: Update the `Popularity` model. `Hype` grows passively via Star Ratings. `Pop` and `Heat` are driven by specific in-ring actions or storyline payoffs.
- **FR-4.2.0 - Opposing Metric Decay**: When a wrestler gains `Pop`, a percentage of their `Heat` is removed (and vice versa). The decay rate is heavily influenced by the wrestler's `backstage.professionalism`, `backstage.ego`, and in-ring style.
- **FR-4.3.0 - Dynamic KayfabeStatus**: Create a `calculate_alignment_status()` function on the Wrestler. 
  - `FACE` = Pop significantly outweighs Heat.
  - `HEEL` = Heat significantly outweighs Pop.
  - `TWEENER` = High Hype, with Pop and Heat within a close margin of each other.
- **FR-4.4.0 - Crowd State**: Add `crowd_excitement` (0-100) to `MatchState`. It shifts dynamically turn-by-turn based on the heat of the executed move.
- **FR-4.5.0 - Post-Match Popularity Shift**: The `MatchReport` outputs `wrestler_stat_deltas` calculating the exact shifts to Hype, Heat, and Pop, utilizing the Opposing Metric Decay.

**Acceptance Criteria**:
- `KayfabeStatus` is a dynamic property, not a static enum field on the database record.
- A Face executing a high-heat "Heel" move gains Heat, which instantly reduces their Pop by a calculated decay factor.
- A wrestler with 90 Pop and 85 Heat (and high Hype) automatically evaluates as a `TWEENER`.

## Logic Blueprint

- **Dynamic KayfabeStatus Logic**:
  - Margin = `abs(Pop - Heat)`
  - If `Margin < 20` and `Hype > 70` -> `TWEENER`
  - Else if `Pop > Heat` -> `FACE`
  - Else -> `HEEL`
- **Opposing Metric Decay**:
  - `Heat_Lost = Pop_Gained * Decay_Multiplier`
  - `Decay_Multiplier` = `f(Ego, Professionalism)`. High professionalism / low ego ("Pure Babyface") means high decay. High ego ("Anti-Hero") means low decay, allowing them to hold both stats.

## File Impact List

- `[MODIFY]` `src/models/wrestler/wrestler.py`
- `[MODIFY]` `src/engine/models/match_state.py`
- `[MODIFY]` `src/engine/models/match_report.py`
- `[MODIFY]` `src/engine/match_simulator.py`

## Agent Assignments

- **To Road Agent**: Draft the DLR. Define the exact math for `calculate_alignment_status()` and the "Opposing Metric Decay" formula. 
- **To The Booker**: *(Future Step)* Implement the math in `match_simulator.py`. 
- **To The Referee**: *(Future Step)* Write tests verifying that gaining Pop destroys Heat, and that Tweeners are correctly evaluated.
