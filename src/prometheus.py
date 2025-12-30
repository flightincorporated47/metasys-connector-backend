# src/prometheus.py
from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from src.metrics import metrics


class PrometheusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return

        snapshot = metrics.snapshot()

        lines = []
        for key, value in snapshot.items():
            lines.append(f"# TYPE {key} counter")
            lines.append(f"{key} {value}")

        body = "\n".join(lines).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # silence default HTTP logs
        return


def start_prometheus_server(port: int):
    server = HTTPServer(("0.0.0.0", port), PrometheusHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server