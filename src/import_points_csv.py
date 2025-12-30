# src/import_points_csv.py
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from src.schema_validate import validate_config
from src.utils.paths import ensure_under_generated
from src.utils.safe_write import atomic_write_text
from src.utils.manifest import write_manifest
from src.utils.last_good import write_last_good


REQUIRED_COLS = [
    "asset_id",
    "asset_name",
    "point_id",
    "point_name",
    "data_type",
    "tier",
    "source_ref",
]

OPTIONAL_COLS = [
    "deadband",
    "min_publish_seconds",
]


def _die(msg: str) -> None:
    raise SystemExit(f"[ERROR] {msg}")


def _to_int(value: str, field: str, rownum: int) -> int:
    try:
        return int(value)
    except Exception:
        _die(f"Row {rownum}: '{field}' must be an integer, got: {value!r}")


def _to_float(value: str, field: str, rownum: int) -> float:
    try:
        return float(value)
    except Exception:
        _die(f"Row {rownum}: '{field}' must be a number, got: {value!r}")


def _norm(s: str) -> str:
    return (s or "").strip()


def _read_csv(csv_path: Path) -> List[Dict[str, str]]:
    if not csv_path.exists():
        _die(f"CSV not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            _die("CSV has no header row.")

        header = [h.strip() for h in reader.fieldnames]
        missing = [c for c in REQUIRED_COLS if c not in header]
        if missing:
            _die(
                "CSV missing required columns: "
                + ", ".join(missing)
                + "\nRequired columns are: "
                + ", ".join(REQUIRED_COLS)
                + "\nOptional columns: "
                + ", ".join(OPTIONAL_COLS)
            )

        rows: List[Dict[str, str]] = []
        for idx, row in enumerate(reader, start=2):  # row 1 is header
            r = {k: (v or "") for k, v in row.items()}
            r["_rownum"] = str(idx)  # preserve original row number for better errors
            rows.append(r)
        return rows


def _build_assets(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Build metasys.assets[] with points[] from CSV rows.
    Groups by (asset_id, asset_name).
    """
    grouped: Dict[Tuple[str, str], List[Dict[str, str]]] = defaultdict(list)

    # basic validation + grouping
    for r in rows:
        rownum = int(_norm(r.get("_rownum", "0")) or "0")
        asset_id = _norm(r["asset_id"])
        asset_name = _norm(r["asset_name"])
        point_id = _norm(r["point_id"])
        point_name = _norm(r["point_name"])
        data_type = _norm(r["data_type"]).lower()
        tier_s = _norm(r["tier"])
        source_ref = _norm(r["source_ref"])

        if not asset_id:
            _die(f"Row {rownum}: asset_id is required.")
        if not asset_name:
            _die(f"Row {rownum}: asset_name is required.")
        if not point_id:
            _die(f"Row {rownum}: point_id is required.")
        if not point_name:
            _die(f"Row {rownum}: point_name is required.")
        if data_type not in ("float", "int", "bool", "string", "enum"):
            _die(
                f"Row {rownum}: data_type must be one of float,int,bool,string,enum. Got: {data_type!r}"
            )

        tier = _to_int(tier_s, "tier", rownum)
        if tier not in (1, 2, 3):
            _die(f"Row {rownum}: tier must be 1, 2, or 3. Got: {tier}")

        if not source_ref:
            _die(f"Row {rownum}: source_ref is required (put REPLACE_ME if unknown).")

        grouped[(asset_id, asset_name)].append(r)

    # build output
    assets: List[Dict[str, Any]] = []
    for (asset_id, asset_name), points_rows in sorted(grouped.items(), key=lambda x: x[0]):
        points: List[Dict[str, Any]] = []

        for r in points_rows:
            rownum = int(_norm(r.get("_rownum", "0")) or "0")
            p: Dict[str, Any] = {
                "point_id": _norm(r["point_id"]),
                "name": _norm(r["point_name"]),
                "data_type": _norm(r["data_type"]).lower(),
                "tier": _to_int(_norm(r["tier"]), "tier", rownum),
                "source_ref": _norm(r["source_ref"]),
            }

            deadband = _norm(r.get("deadband", ""))
            if deadband != "":
                p["deadband"] = _to_float(deadband, "deadband", rownum)

            min_pub = _norm(r.get("min_publish_seconds", ""))
            if min_pub != "":
                p["min_publish_seconds"] = _to_int(min_pub, "min_publish_seconds", rownum)

            points.append(p)

        # stable sort by tier then point name
        points.sort(key=lambda p: (p.get("tier", 2), p.get("name", ""), p.get("point_id", "")))

        assets.append({"asset_id": asset_id, "name": asset_name, "points": points})

    return assets


def _read_text_with_fallback(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1252"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    _die(f"Could not decode base config file: {path} (try saving as UTF-8)")
    raise AssertionError("unreachable")


def _normalize_replace_me(rows: List[Dict[str, str]], allow: bool) -> None:
    """
    If allow==False: fail if any source_ref contains REPLACE_ME.
    If allow==True : convert plain 'REPLACE_ME' into 'metasys:ref:REPLACE_ME' for convenience.
    """
    offenders: List[int] = []
    for r in rows:
        rownum = int(_norm(r.get("_rownum", "0")) or "0")
        sr = _norm(r.get("source_ref", ""))
        if "replace_me" in sr.lower():
            if sr.lower() == "replace_me":
                r["source_ref"] = "metasys:ref:REPLACE_ME"
            offenders.append(rownum)

    if offenders and not allow:
        preview = ", ".join(str(n) for n in offenders[:15])
        more = "" if len(offenders) <= 15 else f" (+{len(offenders)-15} more)"
        _die(
            "CSV contains REPLACE_ME placeholders in source_ref (not allowed without --allow-replace-me).\n"
            f"Rows: {preview}{more}\n"
            "Fix: replace those source_ref values with real Metasys references, or rerun with --allow-replace-me."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate metasys.assets config from CSV.")
    parser.add_argument(
        "--base",
        required=True,
        help="Base YAML config to copy (keeps connector/metasys/ingest/etc).",
    )
    parser.add_argument("--csv", required=True, help="CSV file with point list.")
    parser.add_argument(
        "--out",
        default="config/generated/pilot_generated.yml",
        help="Output YAML path (default: config/generated/pilot_generated.yml).",
    )
    parser.add_argument(
        "--schema",
        default="schemas/metasys_connector_config.schema.json",
        help="Path to JSON schema for validation.",
    )
    parser.add_argument(
        "--allow-replace-me",
        action="store_true",
        help="Allow source_ref containing REPLACE_ME placeholders without failing.",
    )
    args = parser.parse_args()

    base_path = Path(args.base)
    csv_path = Path(args.csv)
    out_path = ensure_under_generated(Path(args.out))
    schema_path = Path(args.schema)

    if not base_path.exists():
        _die(f"Base config not found: {base_path}")
    if not csv_path.exists():
        _die(f"CSV not found: {csv_path}")
    if not schema_path.exists():
        _die(f"Schema not found: {schema_path}")

    # Load base YAML with encoding fallback
    base_text = _read_text_with_fallback(base_path)
    base_cfg = yaml.safe_load(base_text) or {}

    # Load CSV rows
    rows = _read_csv(csv_path)

    # Enforce / normalize REPLACE_ME policy
    _normalize_replace_me(rows, allow=bool(args.allow_replace_me))

    # Build assets structure and attach to config
    assets = _build_assets(rows)
    if "metasys" not in base_cfg or not isinstance(base_cfg["metasys"], dict):
        base_cfg["metasys"] = {}
    base_cfg["metasys"]["assets"] = assets

    # Validate before writing
    validate_config(base_cfg, schema_path=str(schema_path))

    # Two-phase commit YAML write
    out_text = yaml.safe_dump(base_cfg, sort_keys=False, allow_unicode=True)
    atomic_write_text(out_path, out_text)

    # Manifest + LAST_GOOD
    manifest_path = write_manifest(
        out_yaml_path=out_path,
        out_yaml_text=out_text,
        base_path=base_path,
        csv_path=csv_path,
        schema_path=schema_path,
        assets=assets,
    )
    print(f"[OK] Manifest written: {manifest_path}")
    last_good = write_last_good(out_path)
    print(f"[OK] LAST_GOOD updated: {last_good}")

    print(f"[OK] Generated config: {out_path}")
    print(f"[OK] Assets: {len(assets)} | Points: {sum(len(a['points']) for a in assets)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



