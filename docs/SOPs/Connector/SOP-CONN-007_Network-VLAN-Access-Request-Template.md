\# SOP-CONN-006 — Pilot Point Selection Criteria (CSUDH Pilot)



\*\*Status:\*\* Draft (Pilot)  

\*\*Site:\*\* CSUDH  

\*\*Scope:\*\* Standard rules for selecting 100–300 points for pilot usefulness + safe traffic  

\*\*Owner:\*\* Facilities BAS / Energy \& Analytics  

\*\*Last Updated:\*\* 2025-12-31



\## Goal

Select a point set that proves:

\- Data accuracy

\- Operator usefulness (“What do I do next?”)

\- Reasonable traffic (tiered polling + deadbands)

\- Easy expansion path after success



\## Target Pilot Size

\- \*\*100–300 points total\*\*

\- Aim for a mix:

&nbsp; - 20–40% fast

&nbsp; - 40–60% medium

&nbsp; - 10–30% slow



\## Include These Point Types (High Value)

\### Operational Status \& Alarms (usually fast/medium)

\- Equipment enable/disable status

\- Fan/pump status

\- Alarm/fault status, safety trips

\- Mode/state (auto/hand/off, heating/cooling)



\### Core Analog Readings (tier by behavior)

\- Temps: supply/return, leaving/entering water, SAT/MAT (where relevant)

\- Pressures: differential pressure, suction/discharge if applicable

\- Flow estimates if validated

\- kW / kWh / demand points (medium/slow depending on use)



\### Setpoints \& Commanded Values (medium/slow)

\- Setpoints that explain behavior (but avoid points that change constantly unless needed)

\- Output commands where available (read-only view)



\## Avoid These (Pilot Killers)

\- Extremely noisy analog points without deadband tuning

\- “Chatty” values (tiny fluctuations) unless you apply deadband

\- Duplicate points (same value in multiple places)

\- Points that require specialized context to interpret (save for Phase 2)



\## Tier Assignment Rules (Simple)

\- \*\*FAST (5s):\*\* statuses/alarms + a small set of “operational truth” analogs  

\- \*\*MED (30s):\*\* most supervisory analogs and key setpoints  

\- \*\*SLOW (300s):\*\* trend-only, energy totals, rarely changing values



\## Deadband Rules (Default)

\- Status points: publish on change only (deadband effectively not needed)

\- Analog points:

&nbsp; - Start at \*\*1.0%\*\* (or appropriate absolute rule later)

&nbsp; - Increase for noisy sensors

&nbsp; - Decrease for stable critical readings



\## Validation Checklist (Before Go-Live)

\- Sample 10–20 points: confirm units + reasonable range

\- Confirm point names/IDs are stable identifiers (won’t change weekly)

\- Confirm tier distribution isn’t “all fast”

\- Confirm expected traffic estimate is within pilot comfort



\## Evidence Required

\- Pilot selection summary:

&nbsp; - total points

&nbsp; - counts per tier

&nbsp; - top 10 “operator critical” points

\- Rationale: why these points prove value at CSUDH



