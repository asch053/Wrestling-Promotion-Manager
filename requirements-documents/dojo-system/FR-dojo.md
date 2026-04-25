# Dojo, Scouting & Talent Recruitment - Executive Summary

The future of the promotion depends on its foundation. This feature introduces the **Dojo**, a specialized training environment for scouting and developing new talent. Players must manage their Dojo's prestige, equipment, and staff to produce the next generation of main eventers.

---

> **NOTE (v1.1)**: Architecture decision — `DojoStyle` and `WrestlerStyle` are introduced as **extensible Enums**. The current set covers the foundational archetypes. The system is explicitly designed to allow new styles to be added in future updates without breaking existing data.

---

## High-Level Requirements (HLR) Document

**Feature ID**: F-011
**Feature Name**: Dojo, Scouting & Talent Recruitment
**Description**: Implements a persistent training facility (Dojo) that generates new rookie talent every 4 turns and provides a training bonus to assigned wrestlers. Each Dojo has a signature `DojoStyle` that biases the type of talent it produces. Players invest in equipment and scouting to improve the quality of the "Dojo Class."

**User Stories**:
- As a Promoter, I want to invest in a Dojo so I don't have to rely solely on expensive veteran contracts.
- As a Scout, I want my `scouting_skill` to directly impact the quality of the rookies we find.
- As a Trainer, I want my `training_skill` to accelerate the growth of students assigned to the Dojo.
- As a Promoter, I want to invest in different Dojo Styles to build a diverse roster.
- As a Promoter, I want to upgrade Dojo equipment to increase capacity and training efficiency.
- As a Promoter, I want to see my Dojo's prestige grow when graduates succeed on the main roster.
- As a Money Man, I need to track the weekly maintenance costs of the Dojo facility.

**Functional Requirements**:
- **FR-11.1.0 - Dojo Model**: Track `name`, `style` (DojoStyle), `prestige_stars` (0-5), `equipment_level` (1-5), `appeal` (0-100), and `xp`.
- **FR-11.2.0 - Dojo Manager**: Each Dojo has a manager with `scouting_skill` and `training_skill`.
- **FR-11.3.0 - DojoStyle (Extensible Enum)**: Each Dojo specializes in a style that biases the stats and `WrestlerStyle` of graduates:
  - `STRONG_STYLE` — produces heavy hitters (biased: Strength, Stamina, Mean Streak).
  - `TECHNICAL` — produces grapplers (biased: Work Rate, Intelligence).
  - `LUCHA` — produces high-flyers (biased: Agility, Selling).
  - `BRAWLER` — produces streetfighters (biased: Strength, Mean Streak, dirty tricks).
  - `SHOWMAN` — produces entertainers (biased: Heat/Pop generation, Charisma).
  - *(Extensible: future styles like SUBMISSION, HIGHSPOT, etc. can be appended to the Enum)*.
- **FR-11.4.0 - WrestlerStyle (Extensible Enum)**: Each `Wrestler` model carries a `style` attribute:
  - `HEAVY_HITTER`, `GRAPPLER`, `HIGH_FLYER`, `BRAWLER`, `SHOWMAN`, `DIRTY_TRICKS`, `MEAN_STREAK`.
  - *(Future styles are additive; no existing logic breaks when new styles are added)*.
- **FR-11.5.0 - Talent Generation**: Every 4 game-turns, generate a 'Class' of 1-3 rookies.
  - Stats are randomized but weighted by `scouting_skill`.
  - Style is biased by the `DojoStyle` (80% chance of matching style, 20% chance of a random style — representing surprises).
  - Rookies with higher "Potential" are more likely in high-prestige/high-appeal dojos.
- **FR-11.6.0 - Training System**: Wrestlers assigned to a Dojo receive a weekly bonus to `InRingSkill` and `Psychology`.
  - **Formula**: $Stat\_Increase = (Training\_Skill \times 0.1) + (Equipment\_Level \times 0.05)$.
  - The **stat targets** for growth are biased by the Dojo's style (e.g., a LUCHA Dojo grows Agility faster).
- **FR-11.7.0 - Prestige XP Loop**: 
  - Graduate wins a match: +5 XP.
  - Graduate wins a Title: +50 XP.
  - XP thresholds for `prestige_stars` (e.g., 500 XP per star).
- **FR-11.8.0 - Dojo Capacity**: `Capacity = prestige_stars * 2 + equipment_level`.
- **FR-11.9.0 - Financial Integration**: 
  - Weekly Maintenance: $Maintenance = (equipment_level \times 1000) + (prestige_stars \times 500)$.
  - Upgrade Costs: One-time capital expenditure for equipment/marketing.
- **FR-11.10.0 - Multi-Dojo Support**: The `Company` model holds a `List[Dojo]`. Players can own, found, affiliate, or shut down multiple Dojos simultaneously. No limit is enforced in v1.

**Acceptance Criteria**:
- A STRONG_STYLE Dojo should produce wrestlers with higher Strength than a LUCHA Dojo.
- A Level 5 equipment Dojo should allow more students than a Level 1 Dojo.
- A high-training-skill manager should result in faster stat growth for students.
- New rookies should appear every 4 turns in the Dojo's student roster, not the main roster.
- Maintenance costs for all owned Dojos should appear in the weekly financial report.

## Logic Blueprint

- **Training Growth**: $(Training\_Skill \times 0.1) + (Equipment\_Level \times 0.05)$ applied to style-biased target stats.
- **Scouting Weight**: Starting stats = $Base(30-50) + (Scouting\_Skill \times 0.2) + Style\_Bias$.
- **Style Bias Table** (Bonus to listed stats at generation): 
  - `STRONG_STYLE`: +strength, +stamina
  - `TECHNICAL`: +work_rate, +intelligence
  - `LUCHA`: +agility, +selling
  - `BRAWLER`: +strength, +ego (mean streak proxy)
  - `SHOWMAN`: +heat (innate crowd connection), +selling
- **Maintenance Cost**: $(Equipment\_Level \times 1000) + (Prestige\_Stars \times 500)$ per Dojo.

## File Impact List

- `[NEW]` `src/models/promotion/dojo.py` — `DojoStyle`, `DojoManager`, `Dojo` models.
- `[MODIFY]` `src/models/wrestler/wrestler.py` — Add `WrestlerStyle` enum and `style` field.
- `[MODIFY]` `src/models/promotion/company.py` — Add `dojos: List[Dojo]`.
- `[NEW]` `src/engine/talent_generator.py` — Rookie generation logic with style biases.
- `[NEW]` `src/engine/dojo_engine.py` — Weekly training, XP awarding, and capacity checks.
- `[MODIFY]` `src/engine/financial_engine.py` — Sum Dojo maintenance expenses.

## Agent Assignments

- **To Road Agent**: Draft the DLR. Define the `DojoStyle` stat bias table, the `WrestlerStyle` enum, the `talent_generator.py` probability weights, and the `Dojo` class field-by-field specification.
- **To The Booker**: *(Future)* Implement all new files listed above.
- **To The Referee**: *(Future)* Test that style biases produce statistically distinguishable wrestler types from different Dojos.
