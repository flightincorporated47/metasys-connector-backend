# src/metrics.py
from __future__ import annotations
import threading


class Metrics:
    def __init__(self):
        self._lock = threading.Lock()
        self.points_polled = 0
        self.points_published = 0
        self.batches_published = 0
        self.errors = 0

    def inc_polled(self, n: int = 1):
        with self._lock:
            self.points_polled += n

    def inc_published(self, n: int = 1):
        with self._lock:
            self.points_published += n

    def inc_batches(self, n: int = 1):
        with self._lock:
            self.batches_published += n

    def inc_errors(self, n: int = 1):
        with self._lock:
            self.errors += n

    def snapshot(self):
        with self._lock:
            return {
                "points_polled_total": self.points_polled,
                "points_published_total": self.points_published,
                "batches_published_total": self.batches_published,
                "errors_total": self.errors,
            }


metrics = Metrics()
