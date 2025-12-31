\# SOP-CONN-001 — BACnet Scanner Run (CSUDH Pilot)



\*\*Status:\*\* Draft (Pilot)  

\*\*Site:\*\* CSUDH  

\*\*Scope:\*\* BACnet discovery for inventory + point onboarding (read-only)  

\*\*Owner:\*\* Facilities BAS / Networking  

\*\*Last Updated:\*\* 2025-12-31



\## Applies To

\- BACnet/IP networks used by CSUDH facilities BAS

\- Scanning tools in this repo (BACnet scanner pipeline + validators)



\## Safety \& Guardrails

\- \*\*No control writes.\*\* Discovery only.

\- \*\*Scan only approved subnets/IP ranges\*\* (per CSUDH IT/network approval).

\- Rate-limit scans to avoid network disruption.

\- Do not scan student/residential/unknown VLANs.



\## Required Inputs

\- Approved IP ranges/subnets for the scan

\- Local machine with Python + repo cloned

\- Network access to the target VLAN(s)

\- Output folder path (default: `out/bacnet/`)



\## Tools

\- PowerShell

\- Python venv

\- Repo scripts:

&nbsp; - scanner runner

&nbsp; - `src/bacnet\_scanner/validate\_output.py` (devices.json validator)



\## Pre-Checks

1\. Confirm \*\*which VLAN/subnet\*\* you are scanning (CSUDH IT-approved).

2\. Confirm you have permission and a maintenance window if needed.

3\. Confirm your machine IP is on the correct network / VPN segment.

4\. Confirm repo dependencies installed and venv active.



\## Procedure

1\. \*\*Open PowerShell\*\* and go to repo root.

2\. Activate venv:

&nbsp;  - `.\\.venv\\Scripts\\Activate.ps1`

3\. Run scan (use your scanner command/runner):

&nbsp;  - Example:

&nbsp;    - `python -m src.bacnet\_scanner.run --config config/scanner.yml`

4\. Verify output exists:

&nbsp;  - `out/bacnet/devices.json`

5\. Run validation:

&nbsp;  - `python -m src.bacnet\_scanner.validate\_output --json .\\out\\bacnet\\devices.json`



\## Evidence Required

\- Screenshot or paste of validator output showing `\[OK] Valid`

\- `out/bacnet/devices.json` committed or attached (if allowed), or stored in approved location

\- Notes: scanned range + date/time + who ran it



\## Acceptance Criteria

\- Validator passes

\- Device count looks reasonable (not zero, not wildly inflated)

\- No reported network impact during scan window



\## Rollback / Stop Conditions

Stop immediately if:

\- IT reports network impact

\- Scan appears to hit unapproved ranges

\- Unusual broadcast storms, packet loss, or controller instability observed



\## Post-Run Notes

\- If scan is successful: proceed to \*\*SOP-CONN-003 Points Import + Tiering\*\*

\- If not: log which range failed and escalate to BAS/IT for routing/VLAN access checks



