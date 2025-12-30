# Metasys Connector (ADS/ADX) – Site Management App

## Purpose
Read Metasys points near real-time with minimal traffic by publishing **deltas only** (changes),
using tiered polling, deadbands, batching, and outbound-only TLS to the app ingest endpoint.

## Start Here
- docs/metasys_connector_central_compilation.md (single source of truth)
- config/connector_pilot_central_plant.yml (pilot configuration)
- schemas/metasys_connector_config.schema.json (validation)

## Operating Principles
- Read-only Metasys access
- Outbound-only communications
- No control logic changes
- Queue on failure; replay on restore

## Pilot Goals
- 100–300 points
- Validate accuracy, traffic, and operator usefulness
- Expand only after success
