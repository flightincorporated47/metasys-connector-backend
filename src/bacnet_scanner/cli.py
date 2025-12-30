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
        # accept ip or ip:port
        candidate = p.split(":")[0]
        if candidate.count(".") == 3:
            chunks = candidate.split(".")
            if all(c.isdigit() and 0 <= int(c) <= 255 for c in chunks):
                return p
    return None


async def discover_devices_async(
    local_ip: str, port: int, whois_timeout: int, max_devices: int
) -> List[Dict[str, Any]]:
    """
    Discovers BACnet/IP devices via Who-Is/I-Am using BAC0 async Lite.
    Returns list of dict records.
    """
    # BAC0.lite (async version) expects a running loop; we are inside asyncio.run()
    bacnet = BAC0.lite(ip=local_ip, port=port)


    # Give it a moment to bind and start internal tasks
    await asyncio.sleep(0.5)

    # Trigger discovery
    results = bacnet.whois()

    # Wait for I-Am responses
    await asyncio.sleep(max(1, whois_timeout))

    devices: List[Dict[str, Any]] = []

    discovered = getattr(bacnet, "discoveredDevices", None)

    if isinstance(discovered, dict) and discovered:
        for k, v in discovered.items():
            rec = {"raw_key": str(k), "raw_value": str(v)}
            rec["device_instance"] = _extract_int(str(k))
            rec["address"] = _extract_address(str(v))
            devices.append(rec)
    else:
        # Fallback: preserve raw output so we can improve parsing later
        devices.append({"raw": str(results)})

    if len(devices) > max_devices:
        devices = devices[:max_devices]

    # Clean disconnect
    try:
        bacnet.disconnect()
    except Exception:
        pass

    return devices


async def async_main(config_path: Path) -> int:
    cfg = _load_yaml(config_path)

    scanner = cfg.get("scanner", {})
    network = cfg.get("network", {})
    safety = cfg.get("safety", {})
    output = cfg.get("output", {})

    local_ip = str(network.get("local_ip", "")).strip()
    port = int(network.get("bacnet_port", 47808))
    whois_timeout = int(safety.get("whois_timeout_seconds", 5))
    max_devices = int(safety.get("max_devices", 500))

    out_dir = Path(str(output.get("directory", "./out/bacnet")))
    out_file = str(output.get("filename", "devices.json"))
    _ensure_dir(out_dir)

    if not local_ip:
        raise SystemExit("[ERROR] config.network.local_ip is required (IP of the NIC on the BACnet network).")

    meta = {
        "scan_run_id": f"bacnet-{int(time.time())}",
        "timestamp": _now_iso(),
        "site": scanner.get("site"),
        "building": scanner.get("building"),
        "segment_name": scanner.get("segment_name"),
        "local_ip": local_ip,
        "bacnet_port": port,
    }

    print("[INFO] Starting BACnet discovery")
    print(f"       local_ip={local_ip} port={port} timeout={whois_timeout}s max_devices={max_devices}")

    devices = await discover_devices_async(local_ip, port, whois_timeout, max_devices)

    payload = {"meta": meta, "devices": devices}
    out_path = out_dir / out_file
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"[OK] Wrote: {out_path}")
    print(f"[OK] Device records: {len(devices)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="BACnet Scanner (discovery -> devices.json)")
    ap.add_argument("--config", required=True, help="Path to YAML config.")
    args = ap.parse_args()

    return asyncio.run(async_main(Path(args.config)))


if __name__ == "__main__":
    raise SystemExit(main())
