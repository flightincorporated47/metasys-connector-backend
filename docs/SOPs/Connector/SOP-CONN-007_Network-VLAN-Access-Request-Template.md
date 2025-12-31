<<<<<<< HEAD
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



=======
# SOP-CONN-007 — Network/VLAN Access Request Template (CSUDH Pilot)

**Status:** Draft (Pilot)  
**Site:** CSUDH  
**Scope:** Standard request to CSUDH IT for scan/poll access that stays safe + auditable  
**Owner:** Facilities BAS / Networking Liaison  
**Last Updated:** 2025-12-31

## Purpose
Request the minimum network permissions needed to:
- Run BACnet discovery (approved ranges only)
- Poll Metasys points read-only
- Optionally publish outbound to an ingest endpoint (later)

## Guardrails to State in Every Request
- Read-only access (no writes)
- Outbound-only communications
- Rate-limited scanning
- Approved subnets only
- Pilot scope: 100–300 points

## Required Info to Collect Before Submitting
- Pilot site/building scope (CSUDH area)
- Source machine(s): hostname + IP + MAC (if required)
- Target subnets/VLANs and device IP ranges
- Ports/protocols required

## Template (Copy/Paste)
**Subject:** CSUDH Pilot — BAS Network Access Request (Read-Only Connector + BACnet Discovery)

**Requestor:** <Name / Facilities BAS>  
**Business Purpose:** CSUDH pilot to inventory BAS devices and publish read-only point deltas to a local app for operations improvement.  
**Scope:** 100–300 pilot points; limited buildings/central plant as approved.

**Access Requested:**
1) **BACnet Discovery (Read-only):**
   - Source: <scanner machine IP/VLAN>
   - Target: <approved subnets/IP ranges>
   - Protocol/Ports:
     - BACnet/IP UDP 47808 (default) *(confirm if different at CSUDH)*
   - Notes:
     - Rate-limited scanning
     - Will not scan non-approved ranges

2) **Metasys Read Access (Connector):**
   - Source: <connector machine IP/VLAN>
   - Target: <Metasys host/IP>
   - Protocol/Ports:
     - HTTPS TCP 443 (or specified port)
   - Authentication:
     - API key handled as environment variable; not stored in config files

3) **Outbound Publishing (NOT enabled until approved):**
   - Source: <connector machine IP/VLAN>
   - Target: <ingest endpoint fqdn/ip>
   - Protocol/Ports:
     - HTTPS TCP 443
   - Note: publishing is disabled by default; enablement requires approval + testing.

**Security/Compliance Statements:**
- Read-only, no control writes
- Outbound-only (no inbound holes requested)
- Logs retained for troubleshooting
- Keys/secrets not stored in git/YAML

**Requested Window:**
- <date/time> for scan + validation
- Ongoing pilot polling after successful test

**Success Criteria:**
- No network impact during scan
- Connector can reach Metasys read-only
- Approved outbound route ready for later phase (optional)

**Point of Contact:**
- <Name, phone/email>

## Evidence Required
- Ticket/approval reference number
- Confirmed approved ranges + ports
- Date/time access granted
>>>>>>> 420bea80b47824280ace21b22bf7d4053e8dfdbd
