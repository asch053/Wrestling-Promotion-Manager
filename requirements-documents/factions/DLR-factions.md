# Tag Teams, Factions & Relationships - Detailed Logic Requirements (DLR)

## Traceability Table

| DLR ID | Linked HLR ID | Technical Requirement Explanation | Confirmation Test Case |
| :--- | :--- | :--- | :--- |
| *DLR-6.1.1* | *FR-6.1.0* | Implement `Faction` model tracking `id`, `name`, `leader_id`, `members: List[UUID]`. **Faction no longer stores a static `kayfabe_status`**. A faction's effective kayfabe_status is derived from the dominant kayfabe_status of its members (majority rule using each member's dynamic `kayfabe_status` property). Compute `faction.hype` as the average of its members' hype. | Verify instantiation. Verify a faction of 3 Faces and 1 Heel evaluates as Face-dominant. |
| *DLR-6.2.1* | *FR-6.2.0* | Add `friendships: Dict[UUID, int]` and `rivalries: Dict[UUID, int]` (bounds 0-100) to the `Wrestler` model. Add `faction_id: Optional[UUID]`. | Verify instantiation and type hints. |
| *DLR-6.3.1* | *FR-6.3.0* | `calculate_chemistry(w_a, w_b)`: `Base = 50`. `Score -= (w_a.ego + w_b.ego) / 2`. **KayfabeStatus clash check now uses `wrestler.kayfabe_status` (dynamic property)**: `Score -= 50` if one evaluates as Face and the other as Heel. `Score += (100 - abs(w_a.prof - w_b.prof))`. Positive -> Friendship. Negative -> Rivalry. | Verify two high-Pop wrestlers (both dynamically FACE) generate Friendship. Verify a high-Pop wrestler vs a high-Heat wrestler generates Rivalry. |
| *DLR-6.4.1* | *FR-6.4.0* | `can_join_faction`: True IF the wrestler's **dynamic kayfabe_status** broadly matches the faction's dominant kayfabe_status (i.e., a TWEENER can join either, but a pure FACE cannot join a HEEL-dominant faction) AND (`friendships[leader_id] > 60` OR (`wrestler.hype > 80` and `wrestler.ego < 50`)). | Verify a high-Pop (FACE) wrestler is rejected by a HEEL-dominant faction. Verify a TWEENER can join either. |
| *DLR-6.5.1* | *FR-6.5.0* | `get_bloat_penalty(faction)`: Returns `max(0, len(members) - 4) * 10`. Used to reduce effective hype dynamically. | Verify 6-member faction returns `20` penalty. |
| *DLR-6.6.1* | *FR-6.6.0* | Refactor `BookingSheet`: Deprecate `participants`. Add `teams: List[List[UUID]]`. Adjust Pydantic validation to ensure `len(teams) >= 2`. | Verify `teams` structure can hold `[[w1, w2], [w3, w4]]`. |
| *DLR-6.7.1* | *FR-6.7.0* | Update `match_simulator.py`: Turn loop alternates teams. `attacker = random.choice(team_A)`, `defender = random.choice(team_B)`. If `rivalries[defender] > 50`, `heat_generated` *= `1.5`. | Verify match between rivals results in higher `total_heat`. |

## Technical Specs & Architecture

- **Affected Files**:
  - `src/models/wrestler/faction.py` [NEW]
  - `src/models/wrestler/wrestler.py` [MODIFY]
  - `src/models/promotion/booking/booking_sheet.py` [MODIFY]
  - `src/engine/match_simulator.py` [MODIFY]
  - `src/engine/relationship_engine.py` [NEW]
  - `src/engine/faction_manager.py` [NEW]

- **Data Structures**:
  - `faction.py`:
    - `class Faction(BaseModel)`: `id`, `name`, `leader_id: UUID`, `members: List[UUID]`
    - **REMOVED**: Static `kayfabe_status: KayfabeStatus` field. Replaced with a dynamic method or property `get_dominant_alignment(roster_dict)` that checks the dynamic kayfabe_status of each member.
  - `wrestler.py`:
    - Add `friendships: Dict[UUID, int]` and `rivalries: Dict[UUID, int]`.
    - Add `faction_id: Optional[UUID] = None`.
  - `booking_sheet.py`:
    - Replace `participants: List[UUID]` with `teams: List[List[UUID]]`.

- **Logic Flow**: 
  1. **Relationship Engine**: Runs periodically (or on demand) to evaluate relationships. Calls `wrestler.kayfabe_status` (dynamic property) to determine Face/Heel clash, NOT a stored field. High negative chemistry adds to the `rivalries` dict. High positive adds to `friendships`.
  2. **Faction Joining**: Evaluates rules via `faction_manager.py`. Checks the wrestler's dynamic kayfabe_status against the faction's dominant kayfabe_status. If successful, sets `faction_id`.
  3. **Match Simulator Refactor**: 
     - 1v1 matches will now use `teams=[[UUID_A], [UUID_B]]`.
     - Simulator extracts `team_A` and `team_B` from the `teams` array.
     - Picks a random member from the attacking team, and a random member from the defending team to approximate a Chaotic Tag Team Brawl.
     - Multiplies move heat if the attacker and defender are in each other's `rivalries` dicts.

## Work Order Refinement

- **To The Booker**: 
  - **WARNING**: The `Faction` model no longer stores a static `kayfabe_status`. The `can_join_faction` logic must call `wrestler.kayfabe_status` (a dynamic property) and compare it against the faction's dominant kayfabe_status computed from its members. This means a wrestler whose crowd reactions shift them from Face to Tweener may suddenly become eligible to join a Heel faction.
  - **WARNING**: Changing `participants` to `teams` is a breaking schema change. You MUST update all existing tests to pass nested lists `[[w1], [w2]]` instead of flat lists.
- **To The Referee**: 
  - Ensure the rivalry heat multiplier correctly translates to higher Star Ratings.
  - Test that a wrestler whose Pop/Heat balance shifts mid-career correctly evaluates against faction kayfabe_status checks.

## Referee Handbook (QA Scenarios)

- **Positive Tests**:
  - `test_relationship_chemistry`: Pass in two wrestlers with high Pop (both dynamically FACE). Verify Friendship score is high. Pass in a high-Pop wrestler vs a high-Heat wrestler. Verify Rivalry is high.
  - `test_faction_join`: Verify the boolean logic correctly filters valid/invalid applicants using dynamic kayfabe_status.
  - `test_tweener_faction_flexibility`: A TWEENER (Pop ≈ Heat) should be able to join either a Face-dominant or Heel-dominant faction.
- **Match Simulation Tests**:
  - `test_tag_team_simulation`: Pass a 2v2 setup. Assert the simulator doesn't crash and generates a play-by-play involving all 4 wrestlers.
  - `test_rivalry_heat_boost`: Assert the exact same match generates significantly higher heat/star rating when the two competitors have a high rivalry score.
