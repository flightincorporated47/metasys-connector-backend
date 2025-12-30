# src/main.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

import yaml

from src.schema_validate import validate_config
from src.planner import build_poll_plan, summarize_plan
from src.health import start_health_server
from src.prometheus import start_prometheus_server
from src.utils.root_guard import require_project_root


def _load_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}


def main() -> int:
    # Ensure we are running from the project root and normalize CWD.
    require_project_root()

    parser = argparse.ArgumentParser(description="Metasys Connector Runner")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to YAML config (usually config/generated/*.yml).",
    )
    parser.add_argument(
        "--schema",
        default="schemas/metasys_connector_config.schema.json",
        help="Schema path.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate + print plan, then exit.",
    )
    args = parser.parse_args()

    cfg_path = Path(args.config)
    schema_path = Path(args.schema)

    cfg = _load_yaml(cfg_path)

    # 1) Validate config
    validate_config(cfg, schema_path=str(schema_path))

    # 2) Build poll plan
    plan = build_poll_plan(cfg)
    by_tier, total = summarize_plan(plan)

    print("\n=== Poll Plan Summary ===")
    print(f"Config: {cfg_path}")
    print(f"Total points: {total}")
    for tier in sorted(by_tier):
        print(f"Tier {tier}: {by_tier[tier]} points")

    # 3) Start health + metrics servers
    health_port = int(cfg.get("health", {}).get("port", 8081))
    metrics_port = int(cfg.get("prometheus", {}).get("port", 8082))
    start_health_server(health_port)
    start_prometheus_server(metrics_port)

    print(f"\nHealth:     http://localhost:{health_port}/health")
    print(f"Prometheus: http://localhost:{metrics_port}/metrics")

    # If dry-run, stop here (do NOT import Poller / requests / etc.)
    if args.dry_run:
        print("\n[INFO] Dry-run complete. Exiting.")
        return 0

    # Import runtime components only when actually
