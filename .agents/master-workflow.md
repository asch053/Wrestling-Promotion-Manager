# Backstage Operational Manual

This knowledge base defines the workflow for all agents to ensure no "botches" occur during development. It enforces a strict lifecycle and handoff protocol for any new feature in the Wrestling Promotion Manager.

## 1. The Roster (Who is Who)

- **Executive Chairman**: The visionary. Authorizes High-Level Requirements (HLR).
- **Road Agent**: The architect. Translates vision into Detailed Logic Requirements (DLR) and maps tests.
- **The Booker (Talent Agent)**: The math genius. Codes the in-ring simulation logic.
- **The Money Man (Money Agent)**: The treasurer. Manages the database and promotion finances.
- **Fan Experience Architect (Fan Agent)**: The face. Builds the FastAPI bridge and UI/UX schemas.
- **Referee Agent (Team of Refs)**: The enforcer. Writes automated pytest suites based on the DLR.
- **Gorilla Position**: The gatekeeper. Performs the final code review before the "main event" (merging).

## 2. The Production Pipeline (The Handoff)

Every feature must follow this strict sequence:

**Step 1: The Booking Meeting (Chairman)**
- **Chairman ➡️ Road Agent**: The Chairman receives your idea and delivers the HLR document at `./requirements-documents/[feature-name]/FR-[feature-name].md`.
- **Checkpoint:** 🛑 **USER REVIEW REQUIRED** - Do not proceed until the user approves the HLR.

**Step 2: Technical Scripting (Road Agent)**
- **Road Agent ➡️ Engineering Team**: Delivers the DLR at `./requirements-documents/[feature-name]/DLR-[feature-name].md`. This includes technical work orders for the Booker, Money Man, and Fan Architect.
- **Road Agent ➡️ Referee Agent**: Passes the Test Case Design section of the DLR to the Refs so they can prepare empty test suites.
- **Checkpoint:** 🛑 **USER REVIEW REQUIRED** - Do not proceed until the user approves the DLR.

**Step 3: The Scrimmage (Referees)**
- **Trigger:** User approval of the DLR.
- **Referee Agent:** Generates the empty `pytest` files based on the DLR's "Confirmation Test Cases."

**Step 4, 5, & 6: The Build (Engineering Team)**
- **The Money Man**: Builds the SQLAlchemy models, Pydantic schemas, and financial math.
- **The Booker**: Implements the simulation logic in `src/engine/` and `src/models/`.
- **Fan Architect**: Builds the FastAPI endpoints and API schemas.

**Step 7: Verification & The Go-Home Show**
- **Engineering Team ➡️ Referee Agent**: Once code is written in `src/`, it is handed back to the Refs for automated verification (running the tests).
- **Referee Agent ➡️ Gorilla Position**: Submits test results and coverage reports.
- **Gorilla Position ➡️ User**: Conducts final code review and provides the final "Green Light" or "Re-Shoot" verdict.
- **Checkpoint:** 🛑 **USER REVIEW REQUIRED** - Final approval from the user to accept the feature implementation.
