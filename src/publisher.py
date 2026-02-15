# src/publisher.py
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


@dataclass
class Event:
    asset_id: str
    point_id: str
    value: Any
    ts: float
    quality: str
    source_ref: str


class FileQueue:
    """
    Simple disk queue for failed publish batches.

    Each batch is stored as a single JSON file in `path/`.
    Drain order is chronological by filename.
    """

    def __init__(self, path: str, max_disk_mb: int = 500, drop_policy: str = "oldest") -> None:
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.max_bytes = int(max_disk_mb) * 1024 * 1024
        self.drop_policy = (drop_policy or "oldest").lower()

    def _files(self) -> List[Path]:
        return sorted([p for p in self.path.glob("*.json") if p.is_file()], key=lambda p: p.name)

    def _disk_bytes(self) -> int:
        total = 0
        for p in self._files():
            try:
                total += p.stat().st_size
            except FileNotFoundError:
                pass
        return total

    def _enforce_limit(self) -> None:
        if self.max_bytes <= 0:
            return
        if self.drop_policy not in ("oldest", "drop_new"):
            self.drop_policy = "oldest"

        total = self._disk_bytes()
        if total <= self.max_bytes:
            return

        if self.drop_policy == "drop_new":
            # handled by caller (skip enqueue)
            return

        # drop oldest until under limit
        for p in self._files():
            if total <= self.max_bytes:
                break
            try:
                size = p.stat().st_size
                p.unlink(missing_ok=True)
                total -= size
            except FileNotFoundError:
                continue

    def enqueue(self, batch: Dict[str, Any]) -> bool:
        # if policy is drop_new and we're already over budget, skip enqueue
        if self.drop_policy == "drop_new" and self._disk_bytes() > self.max_bytes:
            return False

        ts = int(time.time() * 1000)
        fname = f"{ts}_{uuid.uuid4().hex}.json"
        tmp = self.path / (fname + ".tmp")
        final = self.path / fname
        tmp.write_text(json.dumps(batch), encoding="utf-8")
        tmp.replace(final)

        self._enforce_limit()
        return True

    def drain(self, limit: int = 10) -> List[Tuple[Path, Dict[str, Any]]]:
        out: List[Tuple[Path, Dict[str, Any]]] = []
        for p in self._files()[: max(0, int(limit))]:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                # bad file; drop it
                p.unlink(missing_ok=True)
                continue
            out.append((p, data))
        return out


class Publisher:
    """
    Publisher supports three modes:

    - file: append batches to out/batches.jsonl
    - http: POST batches to ingest.endpoint_url (HTTPS encouraged)
    - disabled: do not publish

    If http publish fails and queue.enabled is true, batches are spooled to disk and replayed.
    """

    def __init__(self, cfg: Dict[str, Any]) -> None:
        self.cfg = cfg

        polling_cfg = cfg.get("polling", {})
        ingest_cfg = cfg.get("ingest", {})
        queue_cfg = cfg.get("queue", {})

        self.flush_interval = int(polling_cfg.get("flush_interval_seconds", 5))
        self.max_batch = int(polling_cfg.get("max_points_per_batch", 200))
        self._buf: List[Event] = []
        self._last_flush = time.time()

        self.mode = str(ingest_cfg.get("mode", "file")).lower()
        self.endpoint_url = str(ingest_cfg.get("endpoint_url", "")).strip()
        self.tls_outbound_only = bool(ingest_cfg.get("tls_outbound_only", True))
        self.timeout_seconds = float(ingest_cfg.get("timeout_seconds", 10))

        # Optional auth controls
        api_key_env = ingest_cfg.get("api_key_env") or "INGEST_API_KEY"
        self.api_key = (os.environ.get(str(api_key_env), "") or os.environ.get("INGEST_API_KEY", "")).strip()
        # legacy alias
        self.connector_key = (os.environ.get("CONNECTOR_KEY", "")).strip()

        self.auth_header = str(ingest_cfg.get("auth_header", "Authorization"))
        self.auth_scheme = str(ingest_cfg.get("auth_scheme", "Bearer"))
        self.connector_key_header = str(ingest_cfg.get("connector_key_header", "X-Connector-Key"))

        # File output (file mode, and optional audit in http mode)
        self.out_dir = Path(polling_cfg.get("out_dir", "out"))
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.out_file = self.out_dir / "batches.jsonl"
        self.write_audit_file = bool(ingest_cfg.get("write_audit_file", False))

        # Queue
        self.queue_enabled = bool(queue_cfg.get("enabled", False))
        self.queue: Optional[FileQueue] = None
        if self.queue_enabled:
            qpath = str(queue_cfg.get("path", "./.queue/metasys-connector"))
            max_mb = int(queue_cfg.get("max_disk_mb", 500))
            drop_policy = str(queue_cfg.get("drop_policy", "oldest"))
            self.queue = FileQueue(qpath, max_disk_mb=max_mb, drop_policy=drop_policy)

        self._session = requests.Session()

        # Safety checks
        if self.mode == "http":
            if not self.endpoint_url:
                raise ValueError("ingest.mode is 'http' but ingest.endpoint_url is empty.")
            if self.tls_outbound_only and not self.endpoint_url.lower().startswith("https://"):
                raise ValueError("TLS outbound-only is enabled; ingest.endpoint_url must start with https://")

    def add(self, ev: Event) -> None:
        self._buf.append(ev)
        self._maybe_flush()

    def _maybe_flush(self) -> None:
        now = time.time()
        if len(self._buf) >= self.max_batch or (now - self._last_flush) >= self.flush_interval:
            self.flush()

    def _headers(self) -> Dict[str, str]:
        h: Dict[str, str] = {"Content-Type": "application/json"}

        # Preferred: Authorization: Bearer <key>
        if self.api_key:
            h[self.auth_header] = f"{self.auth_scheme} {self.api_key}"

        # Optional/legacy: X-Connector-Key: <key>
        if self.connector_key:
            h[self.connector_key_header] = self.connector_key

        return h

    def _post(self, batch: Dict[str, Any]) -> Tuple[bool, str]:
        try:
            r = self._session.post(
                self.endpoint_url,
                headers=self._headers(),
                json=batch,
                timeout=self.timeout_seconds,
            )
            if 200 <= r.status_code < 300:
                return True, f"{r.status_code}"
            return False, f"{r.status_code} {r.text[:200]}".strip()
        except Exception as e:
            return False, repr(e)

    def _write_file(self, batch: Dict[str, Any]) -> None:
        with self.out_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(batch) + "\n")

    def _enqueue(self, batch: Dict[str, Any]) -> None:
        if not self.queue_enabled or not self.queue:
            return
        ok = self.queue.enqueue(batch)
        if not ok:
            print("[QUEUE] drop_new policy active; dropped batch")

    def _drain_queue_once(self, limit: int = 5) -> None:
        if not self.queue_enabled or not self.queue or self.mode != "http":
            return
        for path, batch in self.queue.drain(limit=limit):
            ok, detail = self._post(batch)
            if ok:
                path.unlink(missing_ok=True)
                print(f"[QUEUE->PUBLISH] ok {detail} {path.name}")
            else:
                # stop draining on first failure to avoid tight loops
                print(f"[QUEUE->PUBLISH] fail {detail} {path.name}")
                break

    def flush(self) -> None:
        # In http mode, always try to drain queue first
        self._drain_queue_once(limit=5)

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

        if self.mode == "disabled":
            print(f"[PUBLISH:disabled] batch_count={len(self._buf)} (dropped)")
            self._buf.clear()
            self._last_flush = time.time()
            return

        if self.mode == "file":
            self._write_file(batch)
            print(f"[PUBLISH:file] batch_count={len(self._buf)} -> {self.out_file}")
            self._buf.clear()
            self._last_flush = time.time()
            return

        # http mode
        ok, detail = self._post(batch)
        if ok:
            print(f"[PUBLISH:http] ok {detail} batch_count={len(self._buf)}")
            if self.write_audit_file:
                self._write_file(batch)
            self._buf.clear()
            self._last_flush = time.time()
            return

        print(f"[PUBLISH:http] fail {detail} batch_count={len(self._buf)}")
        # queue on failure
        self._enqueue(batch)
        # optionally keep an audit trail even on failure
        if self.write_audit_file:
            self._write_file(batch)
        self._buf.clear()
        self._last_flush = time.time()

    def close(self) -> None:
        self.flush()
        try:
            self._session.close()
        except Exception:
            pass
