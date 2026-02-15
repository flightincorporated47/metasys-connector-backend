#!/usr/bin/env python3
"""Quick Metasys point read smoke-test.

Usage (from repo root):
  docker compose exec connector python /app/tools/test_metasys_read.py <OBJECT_ID>

Notes:
- Uses the same config file the connector runs with: /app/config/pilot_generated.yml
- Uses METASYS_PASSWORD from container env.
"""

import sys
import json
from pathlib import Path

import yaml  # type: ignore

from src.metasys_client import MetasysClient


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python /app/tools/test_metasys_read.py <OBJECT_ID>", file=sys.stderr)
        return 2

    object_id = sys.argv[1].strip()

    cfg_path = Path("/app/config/pilot_generated.yml")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8-sig")) or {}
    client = MetasysClient(cfg)

    try:
        mv = client.read_point(object_id)
    except Exception as e:
        print(json.dumps({"ok": False, "object_id": object_id, "error": str(e)}, indent=2))
        return 1

    print(json.dumps({"ok": True, "object_id": object_id, "result": mv}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
