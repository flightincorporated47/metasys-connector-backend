from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import validate


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate BACnet devices.json against schema")
    ap.add_argument("--json", required=True, help="Path to devices.json")
    ap.add_argument("--schema", default="schemas/bacnet_devices_output.schema.json")
    args = ap.parse_args()

    data = json.loads(Path(args.json).read_text(encoding="utf-8"))
    schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))

    validate(instance=data, schema=schema)
    print(f"[OK] Valid: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
