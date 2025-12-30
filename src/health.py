# src/health.py
from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Any


class HealthState:
    def __init__(self):
        self.started_at = time.time()
        self.last_poll_at = None
        self.last_publish_at = None
        self.last_error = None

    def snapshot(self) -> Dict[str, Any]:
        return {
            "status": "ok" if self.last_error is None else "degraded",
            "started_at": int(self.started_at),
            "uptime_seconds": int(time.time() - self.started_at),
            "last_poll_at": self.last_poll_at,
            "last_publish_at": self.last_publish_at,
            "last_error": self.last_error,
        }


health_state = HealthState()


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return

        payload = json.dumps(health_state.snapshot()).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        # silence default HTTP logging
        return


def start_health_server(port: int):
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

