
# src/metasys_client.py
import os
import requests
from typing import Dict, Any


class MetasysClient:
    def __init__(self, cfg: Dict[str, Any]):
        self.host = cfg["metasys"]["host"].rstrip("/")
        self.auth = cfg["metasys"]["auth"]
        self.session = requests.Session()

        if self.auth["mode"] == "basic":
            self.session.auth = (
                self.auth["username"],
                os.getenv(self.auth["password_env"])
            )

    def read_point(self, source_ref: str) -> Dict[str, Any]:
        """
        source_ref is assumed to be a Metasys object path or ID.
        """
        url = f"{self.host}/api/v6/objects/{source_ref}/attributes/presentValue"
        r = self.session.get(url, timeout=10)
        r.raise_for_status()

        value = r.json()["item"]["presentValue"]

        return {
            "value": value,
            "quality": "good",
        }
