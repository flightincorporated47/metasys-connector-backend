# src/utils/root_guard.py
from __future__ import annotations

import os
from pathlib import Path


def find_project_root(start: Path | None = None) -> Path | None:
    """
    Walk upward from `start` (or cwd) to find a folder that looks like project root.
    Root is defined as containing: src/, config/, schemas/
    """
    cur = (start or Path.cwd()).resolve()
    for _ in range(15):
        if (cur / "src").is_dir() and (cur / "config").is_dir() and (cur / "schemas").is_dir():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def require_project_root() -> Path:
    root = find_project_root()
    if not root:
        cwd = Path.cwd().resolve()
        msg = (
            "\n[ERROR] You are not running from the project root.\n"
            "Expected a folder containing: src/, config/, schemas/\n\n"
            f"Current folder:\n  {cwd}\n\n"
            "Fix:\n"
            "  cd \"C:\\Users\\gduarte\\Downloads\\metasys-connector-main\\metasys-connector-main\"\n"
            "  python -m src.pipeline --csv .\\points.csv --base .\\config\\connector_pilot_central_plant.yml\n"
        )
        raise SystemExit(msg)

    # Normalize process CWD to root so relative paths are always reliable.
    os.chdir(root)
    return root
