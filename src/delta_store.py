from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class DeltaStore:
    """
    Tracks last-seen values per point key and emits deltas based on deadband rules.

    Expected point key: a stable string identifier like the `source_ref` or an internal id.
    Values: numbers/bools/strings (anything JSON-serializable).
    """

    state_path: Optional[str] = None
    _state: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.state_path:
            self._load()

    def _load(self) -> None:
        p = Path(self.state_path)
        if not p.exists():
            self._state = {}
            return
        try:
            self._state = json.loads(p.read_text(encoding="utf-8")) or {}
        except Exception:
            # If state is corrupted, start fresh rather than crashing the poller.
            self._state = {}

    def _save(self) -> None:
        if not self.state_path:
            return
        p = Path(self.state_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self._state, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _is_number(x: Any) -> bool:
        return isinstance(x, (int, float)) and not isinstance(x, bool)

    def should_emit(
        self,
        key: str,
        value: Any,
        *,
        deadband: float = 0.0,
        min_publish_seconds: float = 0.0,
        now: Optional[float] = None,
    ) -> bool:
        """
        Return True if value is a delta worth emitting:
        - First value always emits
        - Numbers emit if abs(delta) >= deadband (or deadband == 0)
        - Non-numbers emit if changed
        - Also emits if min_publish_seconds elapsed since last emit (heartbeat)
        """
        if now is None:
            now = time.time()

        prev = self._state.get(key)
        if not prev:
            return True

        last_val = prev.get("value")
        last_emit = float(prev.get("last_emit", 0.0))

        if min_publish_seconds and (now - last_emit) >= float(min_publish_seconds):
            return True

        if self._is_number(value) and self._is_number(last_val):
            if float(deadband or 0.0) <= 0.0:
                return float(value) != float(last_val)
            return abs(float(value) - float(last_val)) >= float(deadband)

        return value != last_val

    def update(
        self,
        key: str,
        value: Any,
        *,
        emitted: bool,
        now: Optional[float] = None,
    ) -> None:
        if now is None:
            now = time.time()

        prev = self._state.get(key, {})
        prev["value"] = value
        prev["last_seen"] = now
        if emitted:
            prev["last_emit"] = now
        self._state[key] = prev
        self._save()
