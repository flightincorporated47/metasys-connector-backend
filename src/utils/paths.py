# src/utils/paths.py
from __future__ import annotations

from pathlib import Path


def ensure_under_generated(out_path: Path) -> Path:
    """
    Enforce that generated output stays under config/generated/
    """
    out_path = out_path.resolve()
    gen_dir = (Path.cwd() / "config" / "generated").resolve()

    # Make sure generated dir exists
    gen_dir.mkdir(parents=True, exist_ok=True)

    try:
        out_path.relative_to(gen_dir)
    except ValueError:
        raise SystemExit(
            "\n[ERROR] Refusing to write outside config/generated/.\n"
            f"Requested output:\n  {out_path}\n"
            f"Allowed folder:\n  {gen_dir}\n\n"
            "Fix: set --out to something like:\n"
            "  .\\config\\generated\\pilot_generated.yml\n"
        )
    return out_path
