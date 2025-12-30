
# src/publisher.py
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Event:
    asset_id: str
    point_id: str
    value: Any
    ts: float
    quality: str
    source_ref: str


class Publisher:
    """
    For now: writes batches to ./out/batches.jsonl so you can verify output.
    Next step: HTTPS POST to ingest endpoint.
    """

    def __init__(self, cfg: Dict[str, Any]) -> None:
        self.cfg = cfg
        self.flush_interval = int(cfg["polling"].get("flush_interval_seconds", 5))
        self.max_batch = int(cfg["polling"].get("max_points_per_batch", 200))
        self._buf: List[Event] = []
        self._last_flush = time.time()

        self.out_dir = Path(cfg["polling"].get("out_dir", "out"))
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.out_file = self.out_dir / "batches.jsonl"

    def add(self, ev: Event) -> None:
        self._buf.append(ev)
        self._maybe_flush()

    def _maybe_flush(self) -> None:
        now = time.time()
        if len(self._buf) >= self.max_batch or (now - self._last_flush) >= self.flush_interval:
            self.flush()

    def flush(self) -> None:
        if not self._buf:
            return

        batch = {
            "sent_at": time.time(),
            "count": len(self._buf),
            "events": [
                {
                    "asset_id": e.asset_id,
                    "point_id": e.point_id,
                    "value": e.value,
                    "ts": e.ts,
                    "quality": e.quality,
                    "source_ref": e.source_ref,
                }
                for e in self._buf
            ],
        }

        with self.out_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(batch) + "\n")

        print(f"[PUBLISH] batch_count={len(self._buf)} -> {self.out_file}")
        self._buf.clear()
        self._last_flush = time.time()

    def close(self) -> None:
        self.flush()
