# src/utils/last_good.py
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def write_last_good(out_yaml_path: Path) -> Path:
    gen_dir = out_yaml_path.resolve().parent
    marker = gen_dir / "LAST_GOOD.txt"
    stamp = datetime.now(timezone.utc).isoformat()
    marker.write_text(f"{out_yaml_path.resolve()}\n{stamp}\n", encoding="utf-8")
    return marker
