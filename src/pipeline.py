# src/pipeline.py
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from src.utils.paths import ensure_under_generated
from src.utils.root_guard import require_project_root


def run_step(label: str, args: list[str]) -> None:
    print(f"\n==== {label} ====")
    print("CMD:", " ".join(args))
    result = subprocess.run(args)
    if result.returncode != 0:
        raise SystemExit(f"\n[STOP] Step failed: {label} (exit={result.returncode})")


def main() -> int:
    require_project_root()

    ap = argparse.ArgumentParser(
        description="One-command pipeline: preflight CSV -> import -> validate -> dry-run"
    )
    ap.add_argument("--csv", required=True, help="Path to points CSV (from Excel).")
    ap.add_argument("--base", required=True, help="Base YAML config to merge points into.")
    ap.add_argument(
        "--out",
        default="config/generated/pilot_generated.yml",
        help="Output YAML config path (default: config/generated/pilot_generated.yml).",
    )
    ap.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip CSV preflight step.",
    )
    ap.add_argument(
        "--strict-source-ref",
        action="store_true",
        help="Fail if CSV contains REPLACE_ME in source_ref (strict mode). Default is pilot-friendly (allows REPLACE_ME).",
    )
    args = ap.parse_args()

    # Normalize legacy default if it sneaks in (old path is now forbidden)
    legacy_outs = {
        "config/pilot_generated.yml",
        "config\\pilot_generated.yml",
        ".\\config\\pilot_generated.yml",
        ".\\config/pilot_generated.yml",
    }
    if (args.out or "").strip() in legacy_outs:
        args.out = "config/generated/pilot_generated.yml"

    csv_path = Path(args.csv)
    base_path = Path(args.base)
    out_path = ensure_under_generated(Path(args.out))

    if not csv_path.exists():
        raise SystemExit(f"[ERROR] CSV not found: {csv_path}")
    if not base_path.exists():
        raise SystemExit(f"[ERROR] Base config not found: {base_path}")

    py = sys.executable  # active interpreter

    if not args.skip_preflight:
        run_step(
            "Preflight CSV",
            [py, "-m", "src.preflight_points_csv", "--csv", str(csv_path)],
        )

    # Pilot-friendly default: allow REPLACE_ME placeholders unless strict mode is requested
    import_cmd = [
        py,
        "-m",
        "src.import_points_csv",
        "--base",
        str(base_path),
        "--csv",
        str(csv_path),
        "--out",
        str(out_path),
    ]
    if not args.strict_source_ref:
        import_cmd.append("--allow-replace-me")

    run_step("Import CSV -> Generate YAML", import_cmd)

    run_step(
        "Validate + Dry-run Plan",
        [
            py,
            "-m",
            "src.main",
            "--config",
            str(out_path),
            "--dry-run",
        ],
    )

    print(f"\n✅ DONE. Generated config: {out_path}")
    if args.strict_source_ref:
        print("Mode: STRICT (REPLACE_ME not allowed)")
    else:
        print("Mode: PILOT (REPLACE_ME allowed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
