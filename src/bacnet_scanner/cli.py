# src/bacnet_scanner/cli.py
from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any, Dict, List

import yaml

import BAC0


def _load_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _extract_int(s: str) -> int | None:
    digits = "".join(ch if ch.isdigit() else " " for ch in s).split()
    return int(digits[0]) if digits else None


def _extract_address(s: str) -> str | None:
    parts = s.replace(",", " ").replace(";", " ").split()
    for p in parts:
        candidate = p.split(":")[0]
        if candidate.count(".") == 3:
            chunks = candidate.split(".")
            if all(c.isdigit() and 0 <= int(c) <= 255 for c in chunks):
                return p
    return None


async def discover_devices_async(
    local_ip: str, port: int, whois_timeout: int, max_devices: int
) -> List[Dict[str, Any]]:
    # BAC0 async Lite requires a running event loop (we are inside asyncio.run)
    bacnet = BAC0.lite(ip=local_ip, port=port)

    await asyncio.sleep(0.5)  # allow stack to bind + start tasks
    results = bacnet.whois()
    await asyncio.sleep(max(1, whois_timeout))  # collect I-Am replies

    devices: List[Dict[str, Any]] = []
    discovered = getattr(bacnet, "discoveredDevices", None)

    if isinstance(discovered, dict) and discovered:
        for k, v in discovered.items():
            rec = {
                "device_instance": _extract_int(str(k)),
                "address": _extract_address(str(v)),
                "raw_key": str(k),
                "raw_value": str(v),
            }
            devices.append(rec)
    else:
        devices.append({"raw": str(results)})

    if len(devices) > max_devices:
        devices = devices[:max_devices]

    try:
        bacnet.disconnect()
    except Exception:
        pass

    return devices


async def async_main(config_path: Path, force_offline: bool) -> int:
    cfg = _load_yaml(config_path)

    scanner = cfg.get("scanner", {})
    network = cfg.get("network", {})
    safety = cfg.get("safety", {})
    logging_cfg = cfg.get("logging", {})
    output = cfg.get("output", {})

    local_ip = str(network.get("local_ip", "")).strip()
    port = int(network.get("bacnet_port", 47808))
    whois_timeout = int(safety.get("whois_timeout_seconds", 5))
    max_devices = int(safety.get("max_devices", 500))

    out_dir = Path(str(output.get("directory", "./out/bacnet")))
    out_file = str(output.get("filename", "devices.json"))
    _ensure_dir(out_dir)

    offline_mode = bool(safety.get("offline_mode", False)) or force_offline
    mock_devices = safety.get("mock_devices", []) or []

    bac0_level = str(logging_cfg.get("bac0_log_level", "error")).strip()
    try:
        BAC0.log_level(bac0_level)
    except Exception:
        pass

    meta: Dict[str, Any] = {
        "scan_run_id": f"bacnet-{int(time.time())}",
        "timestamp": _now_iso(),
        "status": "ok",
        "site": scanner.get("site"),
        "building": scanner.get("building"),
        "segment_name": scanner.get("segment_name"),
        "local_ip": local_ip,
        "bacnet_port": port,
        "offline_mode": offline_mode,
    }

    print("[INFO] BACnet scanner starting")
    print(f"       config={config_path}")
    print(f"       offline_mode={offline_mode}")

    devices: List[Dict[str, Any]] = []

    if offline_mode:
        print("[INFO] Offline mode: skipping BACnet bind + discovery.")
        devices = mock_devices
        meta["note"] = "offline_mode enabled; returned mock_devices (if any)."
    else:
        if not local_ip:
            meta["status"] = "error"
            meta["error_type"] = "CONFIG"
            meta["error_message"] = "network.local_ip is required (use IP/prefix, e.g. 172.16.16.22/24)."
        else:
            try:
                print(f"[INFO] Starting BACnet discovery on {local_ip} port={port}")
                devices = await discover_devices_async(local_ip, port, whois_timeout, max_devices)
            except Exception as e:
                meta["status"] = "error"
                meta["error_type"] = type(e).__name__
                meta["error_message"] = str(e)

    meta["device_records"] = len(devices)

    payload = {"meta": meta, "devices": devices}
    out_path = out_dir / out_file
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if meta["status"] == "ok":
        print(f"[OK] Wrote: {out_path}")
        print(f"[OK] Device records: {len(devices)}")
        return 0
    else:
        print(f"[WARN] Wrote (with error status): {out_path}")
        print(f"[WARN] {meta.get('error_type')}: {meta.get('error_message')}")
        return 2


def main() -> int:
    ap = argparse.ArgumentParser(description="BACnet Scanner (devices.json exporter)")
    ap.add_argument("--config", required=True, help="Path to YAML config.")
    ap.add_argument("--offline", action="store_true", help="Force offline_mode regardless of config.")
    args = ap.parse_args()
    return asyncio.run(async_main(Path(args.config), force_offline=args.offline))


if __name__ == "__main__":
    raise SystemExit(main())
