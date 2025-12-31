\# SOP-CONN-002 — Metasys Connector Deploy (Read-Only) (CSUDH Pilot)



\*\*Status:\*\* Draft (Pilot)  

\*\*Site:\*\* CSUDH  

\*\*Scope:\*\* Configure + run Metasys connector read-only with deltas + tiered polling  

\*\*Owner:\*\* Facilities BAS  

\*\*Last Updated:\*\* 2025-12-31



\## Applies To

\- CSUDH pilot environment and selected buildings/central plant equipment

\- Metasys connector runner in this repo



\## Guardrails (Non-Negotiable)

\- \*\*Read-only access\*\* to Metasys.

\- \*\*Outbound-only communications\*\* (TLS where applicable).

\- \*\*No control logic changes\*\*.

\- \*\*Queue on failure + replay on restore\*\* enabled for pilot.



\## Required Inputs

\- Metasys host + port + TLS requirement

\- Pilot projectId (example: `csudh-pilot-central-plant`)

\- API key stored as an environment variable:

&nbsp; - `METASYS\_API\_KEY`



\## Pre-Checks

1\. Confirm CSUDH pilot projectId and target site/building.

2\. Confirm Metasys credentials are read-only and approved.

3\. Confirm network path allows outbound access to Metasys and (if later enabled) ingest endpoint.

4\. Confirm secrets are NOT written to YAML.



\## Procedure

1\. Set secret (PowerShell session):

&nbsp;  - `$env:METASYS\_API\_KEY="\*\*\*"`

2\. Generate/verify connector config YAML (through GUI or CLI).

3\. Validate config against schema (if your repo includes schema validation).

4\. Run in \*\*dry-run\*\* mode first (planning only).

5\. Start connector runtime in local-only mode (publishing disabled).



\## Evidence Required

\- Screenshot/log showing:

&nbsp; - config validated

&nbsp; - dry-run plan summary

&nbsp; - runtime started without errors

\- Project config file reference (path + version)



\## Acceptance Criteria

\- Connector runs without crashes for pilot period

\- No excessive traffic (tiering + deadband doing their job)

\- Delta publishing reduces redundant writes (changes-only behavior)



\## Rollback / Stop Conditions

Stop if:

\- Polling load impacts Metasys performance

\- Authentication errors repeat (possible lockout risk)

\- You see signs of unintended write operations (should never happen)



\## Post-Run Notes

\- If stable: proceed to \*\*SOP-CONN-004 Publishing Enablement Gate\*\* (only when approved)



