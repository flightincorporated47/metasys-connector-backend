\# SOP-CONN-007 — Network/VLAN Access Request Template (CSUDH Pilot)



\*\*Status:\*\* Draft (Pilot)  

\*\*Site:\*\* CSUDH  

\*\*Scope:\*\* Standard request to CSUDH IT for scan/poll access that stays safe + auditable  

\*\*Owner:\*\* Facilities BAS / Networking Liaison  

\*\*Last Updated:\*\* 2025-12-31



\## Purpose

Request the minimum network permissions needed to:

\- Run BACnet discovery (approved ranges only)

\- Poll Metasys points read-only

\- Optionally publish outbound to an ingest endpoint (later)



\## Guardrails to State in Every Request

\- Read-only access (no writes)

\- Outbound-only communications

\- Rate-limited scanning

\- Approved subnets only

\- Pilot scope: 100–300 points



\## Required Info to Collect Before Submitting

\- Pilot site/building scope (CSUDH area)

\- Source machine(s): hostname + IP + MAC (if required)

\- Target subnets/VLANs and device IP ranges

\- Ports/protocols required



\## Template (Copy/Paste)

\*\*Subject:\*\* CSUDH Pilot — BAS Network Access Request (Read-Only Connector + BACnet Discovery)



\*\*Requestor:\*\* <Name / Facilities BAS>  

\*\*Business Purpose:\*\* CSUDH pilot to inventory BAS devices and publish read-only point deltas to a local app for operations improvement.  

\*\*Scope:\*\* 100–300 pilot points; limited buildings/central plant as approved.



\*\*Access Requested:\*\*

1\) \*\*BACnet Discovery (Read-only):\*\*

&nbsp;  - Source: <scanner machine IP/VLAN>

&nbsp;  - Target: <approved subnets/IP ranges>

&nbsp;  - Protocol/Ports:

&nbsp;    - BACnet/IP UDP 47808 (default) \*(confirm if different at CSUDH)\*

&nbsp;  - Notes:

&nbsp;    - Rate-limited scanning

&nbsp;    - Will not scan non-approved ranges



2\) \*\*Metasys Read Access (Connector):\*\*

&nbsp;  - Source: <connector machine IP/VLAN>

&nbsp;  - Target: <Metasys host/IP>

&nbsp;  - Protocol/Ports:

&nbsp;    - HTTPS TCP 443 (or specified port)

&nbsp;  - Authentication:

&nbsp;    - API key handled as environment variable; not stored in config files



3\) \*\*Outbound Publishing (NOT enabled until approved):\*\*

&nbsp;  - Source: <connector machine IP/VLAN>

&nbsp;  - Target: <ingest endpoint fqdn/ip>

&nbsp;  - Protocol/Ports:

&nbsp;    - HTTPS TCP 443

&nbsp;  - Note: publishing is disabled by default; enablement requires approval + testing.



\*\*Security/Compliance Statements:\*\*

\- Read-only, no control writes

\- Outbound-only (no inbound holes requested)

\- Logs retained for troubleshooting

\- Keys/secrets not stored in git/YAML



\*\*Requested Window:\*\*

\- <date/time> for scan + validation

\- Ongoing pilot polling after successful test



\*\*Success Criteria:\*\*

\- No network impact during scan

\- Connector can reach Metasys read-only

\- Approved outbound route ready for later phase (optional)



\*\*Point of Contact:\*\*

\- <Name, phone/email>



\## Evidence Required

\- Ticket/approval reference number

\- Confirmed approved ranges + ports

\- Date/time access granted



