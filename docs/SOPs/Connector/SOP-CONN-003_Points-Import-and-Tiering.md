\# SOP-CONN-003 — Points Import + Tier Assignment (CSUDH Pilot)



\*\*Status:\*\* Draft (Pilot)  

\*\*Site:\*\* CSUDH  

\*\*Scope:\*\* Import points CSV, select 100–300 pilot points, assign polling tiers + deadbands  

\*\*Owner:\*\* Facilities BAS / Analytics  

\*\*Last Updated:\*\* 2025-12-31



\## Applies To

\- CSUDH pilot point onboarding for connector polling



\## Required Inputs

\- Points CSV (approved export format)

\- Tiering rules:

&nbsp; - Fast (e.g., 5s): critical operational points

&nbsp; - Medium (e.g., 30s): normal supervisory points

&nbsp; - Slow (e.g., 300s): trend-only / low priority

\- Default deadband (%), batch size



\## Pre-Checks

1\. Confirm CSV contains stable identifiers (name/path/object id).

2\. Confirm unit sanity (°F, PSI, %, kW) and typical ranges.

3\. Confirm pilot selection aligns with: \*\*accuracy + usefulness + traffic constraints\*\*.



\## Procedure

1\. Import CSV through the UI (Points tab) or CLI tool if you use one.

2\. Select 100–300 points for the pilot.

3\. Assign each point to a tier:

&nbsp;  - Fast: alarms, critical temps/pressures, statuses needed quickly

&nbsp;  - Medium: operational monitoring

&nbsp;  - Slow: trends, setpoints, slowly changing values

4\. Set deadband rules:

&nbsp;  - Use higher deadband for noisy analog points

&nbsp;  - Use near-zero deadband for statuses (but only publish on change)

5\. Save config (version increments).

6\. Generate YAML and confirm:

&nbsp;  - points list populated

&nbsp;  - tier intervals correct

&nbsp;  - deadband defaults applied



\## Evidence Required

\- Saved config version number

\- Generated YAML attached or stored

\- A short note: how many points per tier + rationale



\## Acceptance Criteria

\- Pilot point count within target (100–300)

\- Tier distribution makes sense (not all fast)

\- No “chatter points” flooding deltas (deadband tuned)



\## Rollback / Fix Guidance

\- If too chatty: increase deadband or move point to slower tier

\- If too slow: move only a small set to faster tier (avoid full-fast temptation)



