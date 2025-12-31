\# SOP-CONN-004 — Publishing Enablement Gate (CSUDH Pilot)



\*\*Status:\*\* Draft (Pilot)  

\*\*Site:\*\* CSUDH  

\*\*Scope:\*\* Enable HTTP publishing layer (disabled by default), verify queue + replay, confirm ingest behavior  

\*\*Owner:\*\* Facilities BAS / App Owner  

\*\*Last Updated:\*\* 2025-12-31



\## Default Position

Publishing is \*\*OFF\*\* by default. Enabling it requires explicit approval and verification.



\## Preconditions (Must Be True)

\- Local-only runtime is stable for an agreed period

\- Poll plan reviewed (tiers, batch sizing, deadband)

\- Ingest endpoint reachable and approved (outbound-only)

\- TLS enabled (if endpoint supports it)

\- Failure queue behavior tested



\## Procedure

1\. Configure publishing settings in UI (Publish tab):

&nbsp;  - ingest URL

&nbsp;  - auth token/secret reference (do not store in YAML)

&nbsp;  - enable flag remains OFF until final step

2\. Perform a \*\*connectivity test\*\* (no publishing):

&nbsp;  - confirm DNS/TLS handshake reachable

3\. Enable publishing (final step):

&nbsp;  - flip enable toggle ON

4\. Verify deltas-only behavior:

&nbsp;  - confirm you do not publish full snapshots repeatedly

5\. Test failure queue:

&nbsp;  - temporarily block endpoint / disconnect network

&nbsp;  - confirm queue grows but connector stays stable

&nbsp;  - restore network and confirm replay happens



\## Evidence Required

\- Screenshot/log showing:

&nbsp; - publishing enabled timestamp

&nbsp; - successful POSTs (or upload attempts)

&nbsp; - queue behavior on failure + replay on restore

\- Change record entry (who approved + when)



\## Acceptance Criteria

\- Publishing sends only changes (deltas) at expected cadence

\- Queue persists on failure (if enabled)

\- Replay works without duplicating or dropping events (within reason for pilot)



\## Rollback / Emergency Stop

\- Immediately disable publishing toggle

\- Keep polling local-only

\- Preserve logs + queue files for review



