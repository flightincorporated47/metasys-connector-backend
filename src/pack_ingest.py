# src/pack_ingest.py
from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path
from typing import Any, Dict

from jsonschema import validate


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> int:
    ap = argparse.ArgumentParser(description="Package app-ingestion bundle under out/ingest/")
    ap.add_argument("--out-dir", default="out/ingest", help="Bundle output directory.")
    ap.add_argument("--bacnet-json", default="out/bacnet/devices.json", help="BACnet devices.json path.")
    ap.add_argument(
        "--bacnet-schema",
        default="schemas/bacnet_devices_output.schema.json",
        help="BACnet output schema path.",
    )
    ap.add_argument("--include-metasys", action="store_true", help="Include Metasys artifacts (if present).")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- BACnet validate + copy ---
    bacnet_json = Path(args.bacnet_json)
    bacnet_schema = Path(args.bacnet_schema)

    if not bacnet_json.exists():
        raise SystemExit(f"[ERROR] Missing BACnet JSON: {bacnet_json}")
    if not bacnet_schema.exists():
        raise SystemExit(f"[ERROR] Missing BACnet schema: {bacnet_schema}")

    data = read_json(bacnet_json)
    schema = read_json(bacnet_schema)
    validate(instance=data, schema=schema)

    bacnet_dst_json = out_dir / "bacnet" / "devices.json"
    bacnet_dst_schema = out_dir / "bacnet" / "bacnet_devices_output.schema.json"

    copy_file(bacnet_json, bacnet_dst_json)
    copy_file(bacnet_schema, bacnet_dst_schema)

    files: Dict[str, Any] = {}

    def add_manifest_entry(logical_name: str, path: Path) -> None:
        files[logical_name] = {
            "path": str(path).replace("\\", "/"),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    add_manifest_entry("bacnet.devices_json", bacnet_dst_json)
    add_manifest_entry("bacnet.schema_json", bacnet_dst_schema)

    # --- Metasys (optional; safe if you don't have artifacts yet) ---
    metasys_entries: Dict[str, Any] = {}
    if args.include_metasys:
        metasys_dir = out_dir / "metasys"
        metasys_dir.mkdir(parents=True, exist_ok=True)

        # You can add actual artifacts later (e.g., last poll plan, publish payloads)
        # For now we just create the folder and note it's empty.
        metasys_entries["note"] = "Metasys artifacts not yet bundled. Add when publish payloads are implemented."

    manifest = {
        "bundle": {
            "bundle_id": f"ingest-{int(time.time())}",
            "created_at": now_iso(),
            "version": "0.1",
        },
        "contents": {
            "bacnet": {
                "meta": data.get("meta", {}),
                "device_records": data.get("meta", {}).get("device_records", len(data.get("devices", []))),
            },
            "metasys": metasys_entries if args.include_metasys else None,
        },
        "files": files,
    }

    manifest_path = out_dir / "manifest.json"
    write_json(manifest_path, manifest)

    print("[OK] Ingest bundle created:")
    print(f"     {out_dir}")
    print(f"[OK] Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
