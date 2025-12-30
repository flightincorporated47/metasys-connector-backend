# src/export_config_to_csv.py
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Dict, List

import yaml


HEADERS = [
    "asset_id",
    "asset_name",
    "point_id",
    "point_name",
    "data_type",
    "tier",
    "deadband",
    "min_publish_seconds",
    "source_ref",
]


def die(msg: str) -> None:
    raise SystemExit(f"[ERROR] {msg}")


def norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v)


def main() -> int:
    ap = argparse.ArgumentParser(description="Export metasys.assets points from YAML config to CSV.")
    ap.add_argument("--config", required=True, help="Path to YAML config (validated or generated).")
    ap.add_argument("--out", required=True, help="Output CSV path.")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    out_path = Path(args.out)

    if not cfg_path.exists():
        die(f"Config not found: {cfg_path}")

    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    metasys = cfg.get("metasys", {})
    assets = metasys.get("assets", [])
    if not isinstance(assets, list) or not assets:
        die("No metasys.assets found in config.")

    rows: List[Dict[str, str]] = []

    for a in assets:
        asset_id = norm(a.get("asset_id"))
        asset_name = norm(a.get("name"))
        points = a.get("points", [])
        if not isinstance(points, list):
            continue

        for p in points:
            rows.append(
                {
                    "asset_id": asset_id,
                    "asset_name": asset_name,
                    "point_id": norm(p.get("point_id")),
                    "point_name": norm(p.get("name")),
                    "data_type": norm(p.get("data_type")),
                    "tier": norm(p.get("tier")),
                    "deadband": norm(p.get("deadband")),
                    "min_publish_seconds": norm(p.get("min_publish_seconds")),
                    "source_ref": norm(p.get("source_ref")),
                }
            )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADERS)
        w.writeheader()
        w.writerows(rows)

    print(f"[OK] Exported CSV: {out_path}")
    print(f"[OK] Points exported: {len(rows)} | Assets: {len(assets)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
