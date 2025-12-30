# src/utils/manifest.py
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _tier_counts(assets: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    c = Counter()
    for a in assets:
        for p in a.get("points", []):
            c[str(p.get("tier", ""))] += 1
    return {k: int(c[k]) for k in sorted(c.keys(), key=lambda x: (x == "", x))}


def write_manifest(
    *,
    out_yaml_path: Path,
    out_yaml_text: str,
    base_path: Path,
    csv_path: Path,
    schema_path: Path,
    assets: list[dict[str, Any]],
) -> Path:
    out_yaml_path = out_yaml_path.resolve()
    manifest_path = out_yaml_path.with_suffix(out_yaml_path.suffix + ".manifest.json")

    points_count = sum(len(a.get("points", [])) for a in assets)
    tiers = _tier_counts(assets)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "inputs": {
            "base_config": {"path": str(base_path.resolve()), "sha256": sha256_file(base_path.resolve())},
            "points_csv": {"path": str(csv_path.resolve()), "sha256": sha256_file(csv_path.resolve())},
            "schema": {"path": str(schema_path.resolve()), "sha256": sha256_file(schema_path.resolve())},
        },
        "output": {
            "yaml_path": str(out_yaml_path),
            "yaml_sha256": sha256_text(out_yaml_text),
            "manifest_path": str(manifest_path),
        },
        "counts": {
            "assets": int(len(assets)),
            "points": int(points_count),
            "tiers": tiers,
        },
    }

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path
