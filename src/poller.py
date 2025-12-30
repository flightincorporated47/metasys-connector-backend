
# src/poller.py
from __future__ import annotations

import time
from typing import Any, Dict, List

from src.planner import PlannedPoint
from src.metasys_client import MetasysClient
from src.delta_store import DeltaStore
from src.publisher import Publisher, Event


class Poller:
    def __init__(self, cfg: Dict[str, Any], plan: List[PlannedPoint]) -> None:
        self.cfg = cfg
        self.plan = plan
        self.client = MetasysClient(cfg)
        self.deltas = DeltaStore()
        self.publisher = Publisher(cfg)

        # schedule: next_due per point (simple, robust)
        now = time.time()
        self.next_due = {self._key(p): now for p in plan}

    def _key(self, p: PlannedPoint) -> str:
        return f"{p.asset_id}::{p.point_id}"

    def run_forever(self) -> None:
        while True:
            now = time.time()
            soonest = None

            for p in self.plan:
                k = self._key(p)
                due = self.next_due[k]
                if now >= due:
                    self._poll_one(p, now)
                    self.next_due[k] = now + float(p.poll_seconds)

                soonest = due if soonest is None else min(soonest, due)

            self.publisher.flush()  # allows time-based flush even if no new events

            # sleep a little so we don't spin CPU
            time.sleep(float(self.cfg["polling"].get("tick_seconds", 0.25)))

    def _poll_one(self, p: PlannedPoint, now: float) -> None:
        mv = self.client.read_point(p.source_ref)

        if self.deltas.should_publish(
            key=self._key(p),
            new_value=mv.value,
            new_ts=mv.ts,
            deadband=float(p.deadband),
            min_publish_seconds=int(p.min_publish_seconds),
        ):
            self.publisher.add(
                Event(
                    asset_id=p.asset_id,
                    point_id=p.point_id,
                    value=mv.value,
                    ts=mv.ts,
                    quality=mv.quality,
                    source_ref=p.source_ref,
                )
            )

    def close(self) -> None:
        self.publisher.close()
        self.client.close()
