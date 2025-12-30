# src/run_all.py
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> int:
    print("\n==== RUN ====")
    print("CMD:", " ".join(cmd))
    return subprocess.call(cmd)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run all repo pipelines (BACnet + Metasys)")
    ap.add_argument("--bacnet-config", default="config/bacnet_scanner.yml")
    ap.add_argument("--metasys-csv", default="points.csv")
    ap.add_argument("--metasys-base", default="config/connector_pilot_central_plant.yml")
    ap.add_argument("--skip-metasys", action="store_true")
    ap.add_argument("--skip-bacnet", action="store_true")
    args = ap.parse_args()

    root = Path(".").resolve()
    bacnet_cfg = str((root / args.bacnet_config).resolve())

    rc = 0

    if not args.skip_bacnet:
        rc = run([sys.executable, "-m", "src.bacnet_scanner.cli", "--config", bacnet_cfg])
        if rc != 0:
            return rc

    if not args.skip_metasys:
        rc = run([sys.executable, "-m", "src.pipeline", "--csv", args.metasys_csv, "--base", args.metasys_base])
        if rc != 0:
            return rc

    print("\n✅ DONE: All pipelines completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
