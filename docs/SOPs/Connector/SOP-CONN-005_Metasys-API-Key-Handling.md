\# SOP-CONN-005 — Metasys API Key Handling (CSUDH Pilot)



\*\*Status:\*\* Draft (Pilot)  

\*\*Site:\*\* CSUDH  

\*\*Scope:\*\* Secure handling of Metasys API credentials for connector runtime + local API  

\*\*Owner:\*\* Facilities BAS Lead / App Owner  

\*\*Last Updated:\*\* 2025-12-31



\## Applies To

\- Metasys connector backend runtime (local dev + pilot)

\- Local API server (`uvicorn ... --port 8787`)

\- Any pilot laptops/VMs running the connector



\## Guardrails (Non-Negotiable)

\- \*\*Never store API keys in YAML, JSON, git commits, or screenshots.\*\*

\- \*\*Never paste keys into tickets, chat logs, or SOP evidence.\*\*

\- \*\*Keys must be read-only\*\*, pilot-scoped if possible.

\- Rotate/revoke immediately on suspected exposure.



\## Approved Storage Methods (Pilot)

1\) \*\*Environment Variable (recommended for pilot):\*\*

&nbsp;  - `METASYS\_API\_KEY` in the current PowerShell session (temporary)

2\) \*\*Windows User Environment Variable (if persistent needed):\*\*

&nbsp;  - Set at user scope, not system scope

3\) \*\*Secret Manager (future production):\*\*

&nbsp;  - Azure Key Vault / 1Password / campus-approved secrets platform



\## Not Approved

\- `.env` files committed to repo

\- config YAML fields like `api\_key: ...`

\- Notepad text files

\- Emailing keys



\## Procedure A — Temporary Session Key (Safest for pilot laptops)

1\. Open PowerShell.

2\. Set key only for this session:

&nbsp;  - `$env:METASYS\_API\_KEY="\*\*\*"`

3\. Start backend/local API and connector processes from the same session.

4\. When done, close the PowerShell window (clears env var).



\## Procedure B — Windows User Environment Variable (If you must persist)

1\. Open PowerShell:

&nbsp;  - `\[Environment]::SetEnvironmentVariable("METASYS\_API\_KEY","\*\*\*","User")`

2\. Close and reopen PowerShell to load the new env var.

3\. Verify:

&nbsp;  - `echo $env:METASYS\_API\_KEY`

&nbsp;  - (Do \*\*not\*\* screenshot the output.)



\## Verification (No Leaks)

\- Confirm the UI/Local API reports “secret exists” without ever displaying the value.

\- Confirm generated YAML contains only references (no literal key).



\## Evidence Required (Safe)

\- Screenshot/log line showing “API key configured” or `exists: true` (value must not appear)

\- Who set it + date/time + machine name (if required by your internal process)



\## Rollback / Rotation

\- If suspected exposure: rotate key in Metasys/IdP process immediately.

\- Clear env var:

&nbsp; - `$env:METASYS\_API\_KEY=""`

\- If stored at user scope, remove:

&nbsp; - `\[Environment]::SetEnvironmentVariable("METASYS\_API\_KEY",$null,"User")`



