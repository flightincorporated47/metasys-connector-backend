# Metasys Connector (ADS/ADX) – Central Compilation

This document is the **single source of truth** for how the Metasys Connector is intended to run in the
Site Management App project.

## 1) What the connector does

The connector is a **read-only** data collector for Metasys ADS/ADX.

It:
- Reads point values from Metasys REST API at tiered intervals (fast / medium / slow).
- Applies **deadbands** and **minimum publish intervals** so we publish **deltas only**.
- Batches events into payloads.
- Publishes outbound to the SiteManager ingest endpoint over **TLS (HTTPS)**.
- If publishing fails, it **queues** batches on disk and replays them when connectivity is restored.

It does **not**:
- Write commands to Metasys
- Change Metasys configuration
- Require installing anything on the Metasys server

## 2) Start here (pilot)

Files you will touch first:

- `config/connector_pilot_central_plant.yml` – base config template for the pilot
- `points.csv` – your points list (or `metasys_points_import_template.csv`)
- `schemas/metasys_connector_config.schema.json` – config validation
- `src/main.py` – connector runtime entrypoint

### Quick dry-run (validate + plan only)

```bash
python -m src.main --config config/connector_pilot_central_plant.yml --dry-run
```

### Generate a pilot config from points.csv (recommended)

```bash
python -m src.pipeline --csv points.csv --base config/connector_pilot_central_plant.yml --out config/pilot_generated.yml
python -m src.main --config config/pilot_generated.yml --dry-run
```

### Run the connector (real polling)

```bash
python -m src.main --config config/pilot_generated.yml
```

## 3) Polling model (tiers + deltas)

### Tiered polling
Each point is assigned a tier with an interval:

- Tier 1: 5s (high-churn: flow, pressure, outputs)
- Tier 2: 30s (moderate-churn)
- Tier 3: 300s (slow-churn: zone temps, setpoints)

Tiers are configured in `polling.defaults.tiers`.

### Delta rules
A point publishes only when:
- Absolute change >= `deadband`, AND
- At least `min_publish_seconds` elapsed since the last publish for that point

This avoids hammering Metasys and reduces network/DB traffic.

## 4) Publishing modes

Configured under `ingest.mode`:

- `file` (default): write batches to `polling.out_dir/batches.jsonl` for verification
- `http`: POST batches to `ingest.endpoint_url`
- `disabled`: do not publish (still polls; useful for testing Metasys access)

### Ingest authentication
By default the connector looks for an API key in one of these environment variables:

- `INGEST_API_KEY` (preferred)
- `CONNECTOR_KEY` (legacy alias)

It will send:
- `Authorization: Bearer <key>` (preferred)
- and also `X-Connector-Key: <key>` if you set `CONNECTOR_KEY`

You can override with config keys under `ingest`:
- `api_key_env` (string)
- `auth_header` (string, default `Authorization`)
- `auth_scheme` (string, default `Bearer`)
- `connector_key_header` (string, default `X-Connector-Key`)

## 5) Queue + replay

Configured under `queue`:

- `enabled`: true/false
- `path`: directory for queued batches
- optional:
  - `max_disk_mb` (default 500)
  - `drop_policy`: `oldest` (default) or `drop_new`

When publishing fails (timeout, connection error, non-2xx), the connector writes the batch to disk.
On each tick, it attempts to drain a small number of queued batches first, then publishes new batches.

This ensures:
- no event storms on recovery
- no data loss during short outages (within disk budget)

## 6) Network + security expectations

- Outbound-only traffic from the connector host
- HTTPS required for ingest when `ingest.tls_outbound_only` is true (default)
- Metasys TLS verification controlled by `metasys.verify_tls` (should be true on campus networks)
- Least privilege: Metasys user should be read-only, API-only, scoped to needed objects

## 7) Troubleshooting

### “Nothing is publishing”
- Confirm `ingest.mode` is `http` (not `file` or `disabled`)
- Confirm `INGEST_ENDPOINT` or `ingest.endpoint_url` points to the right URL
- Confirm `INGEST_API_KEY` is set in the container env

### “Metasys login fails”
- Verify `metasys.host`, `api_base`, `username`, and `METASYS_PASSWORD` are correct
- Confirm the Metasys certificate is trusted if `verify_tls: true`

### “Queue is growing”
- Ingest endpoint is unavailable or rejecting payloads
- Check container logs and HTTP status codes
- Increase `queue.max_disk_mb` temporarily or fix endpoint connectivity

## 8) Docker

`docker-compose.yml` expects `metasys-connector/connector.dockerfile`.

Build/run:

```bash
docker compose build connector
docker compose up -d connector
docker compose logs -f --tail=200 connector
```
