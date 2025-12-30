# src/upload_ingest.py
from __future__ import annotations

import argparse
import os
import sys
import zipfile
from pathlib import Path

import requests


def zip_folder(folder: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in folder.rglob("*"):
            if p.is_file():
                z.write(p, arcname=str(p.relative_to(folder)).replace("\\", "/"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Upload out/ingest bundle to app ingest endpoint (disabled by default).")
    ap.add_argument("--bundle-dir", default="out/ingest")
    ap.add_argument("--endpoint", default=os.environ.get("INGEST_ENDPOINT", ""))
    ap.add_argument("--api-key", default=os.environ.get("INGEST_API_KEY", ""))
    ap.add_argument("--enable", action="store_true", help="Required. Without this flag the script will not upload.")
    args = ap.parse_args()

    bundle_dir = Path(args.bundle_dir)

    if not args.enable:
        print("[SAFEGUARD] Upload disabled. Re-run with --enable when you are ready.")
        print("           Example: python -m src.upload_ingest --enable --endpoint https://... --api-key ...")
        return 0

    if not args.endpoint:
        print("[ERROR] Missing endpoint. Provide --endpoint or set INGEST_ENDPOINT env var.")
        return 2

    if not bundle_dir.exists():
        print(f"[ERROR] Bundle dir not found: {bundle_dir}")
        return 2

    zip_path = Path("out") / "ingest_bundle.zip"
    zip_folder(bundle_dir, zip_path)

    headers = {}
    if args.api_key:
        headers["Authorization"] = f"Bearer {args.api_key}"

    with zip_path.open("rb") as f:
        files = {"file": ("ingest_bundle.zip", f, "application/zip")}
        resp = requests.post(args.endpoint, headers=headers, files=files, timeout=60)

    print("[INFO] HTTP status:", resp.status_code)
    print(resp.text[:1000])
    return 0 if 200 <= resp.status_code < 300 else 3


if __name__ == "__main__":
    raise SystemExit(main())
