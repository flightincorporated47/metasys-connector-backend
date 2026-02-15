from __future__ import annotations

import os
import re
from typing import Any, Dict
from urllib.parse import quote

import requests


_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}$"
)


def _looks_like_uuid(s: str) -> bool:
    return bool(_UUID_RE.match(s or ""))


class MetasysClient:
    """
    Minimal Metasys REST client for presentValue reads.

    Supports source_ref formats:
      - "<uuid>"
      - "metasys:ref:<uuid>"
      - "metasys:<uuid>"
    """

    def __init__(self, cfg: Dict[str, Any]):
        m = cfg.get("metasys") or {}
        self.host = (m.get("host") or "").rstrip("/")
        self.api_base = (m.get("api_base") or "/api/v6").rstrip("/")
        self.timeout = float(m.get("timeout_seconds") or 10)

        self.verify_tls = bool(m.get("verify_tls", True))
        ca_bundle = m.get("ca_bundle") or os.getenv("METASYS_CA_BUNDLE")
        self.verify = ca_bundle if ca_bundle else self.verify_tls

        auth = m.get("auth") or {}
        self.session = requests.Session()

        mode = (auth.get("mode") or "").lower()
        if mode == "basic":
            username = auth.get("username") or ""
            pw_env = auth.get("password_env") or ""
            password = os.getenv(pw_env) if pw_env else None
            if not username or not pw_env:
                raise RuntimeError("metasys.auth.username and metasys.auth.password_env are required for basic auth")
            if not password:
                raise RuntimeError(f"Metasys password env var {pw_env!r} is not set")
            self.session.auth = (username, password)

    def _normalize_source_ref(self, source_ref: str) -> str:
        s = (source_ref or "").strip()
        if not s:
            raise RuntimeError("Empty source_ref")
        if "REPLACE_ME" in s:
            raise RuntimeError(f"Invalid object id in source_ref={source_ref!r} (did you forget to replace REPLACE_ME?)")

        if s.startswith("metasys:ref:"):
            s = s[len("metasys:ref:") :]
        elif s.startswith("metasys:"):
            s = s[len("metasys:") :]

        s = s.strip()
        if not _looks_like_uuid(s):
            raise RuntimeError(f"Invalid Metasys object id in source_ref={source_ref!r} (expected UUID)")
        return s

    def read_point(self, source_ref: str) -> Dict[str, Any]:
        obj_id = self._normalize_source_ref(source_ref)
        url = f"{self.host}{self.api_base}/objects/{quote(obj_id)}/attributes/presentValue"

        r = self.session.get(url, timeout=self.timeout, verify=self.verify)
        r.raise_for_status()

        payload = r.json()
        value = payload.get("item", {}).get("presentValue")
        return {"value": value, "quality": "good"}
