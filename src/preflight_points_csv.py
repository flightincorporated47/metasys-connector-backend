# src/preflight_points_csv.py
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


REQUIRED_COLS = [
    "asset_id",
    "asset_name",
    "point_id",
    "point_name",
    "data_type",
    "tier",
    "source_ref",
]

ALLOWED_DATA_TYPES = {"float", "int", "bool", "string", "enum"}
ALLOWED_TIERS = {"1", "2", "3"}


def die(msg: str) -> None:
    raise SystemExit(f"[ERROR] {msg}")


def norm(s: str) -> str:
    return (s or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Preflight a points CSV for the Metasys connector.")
    ap.add_argument("--csv", required=True, help="Path to points CSV (UTF-8 or UTF-8 with BOM).")
    ap.add_argument("--max-missing", type=int, default=50, help="Max missing source_ref rows to print.")
    ap.add_argument("--max-dupes", type=int, default=50, help="Max duplicate keys to print.")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        die(f"CSV not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            die("CSV has no header row.")
        header = [h.strip() for h in reader.fieldnames]
        missing_cols = [c for c in REQUIRED_COLS if c not in header]
        if missing_cols:
            die(f"CSV missing required columns: {', '.join(missing_cols)}")

        rows = list(reader)

    total = len(rows)
    if total == 0:
        die("CSV has no data rows.")

    tier_counts = Counter()
    dtype_counts = Counter()
    missing_source = []
    replace_me = []
    bad_tier = []
    bad_dtype = []
    dupes = defaultdict(int)

    for i, r in enumerate(rows, start=2):  # row 1 is header
        asset_id = norm(r["asset_id"])
        point_id = norm(r["point_id"])
        tier = norm(r["tier"])
        dtype = norm(r["data_type"]).lower()
        src = norm(r["source_ref"])

        key = (asset_id, point_id)
        dupes[key] += 1

        if tier:
            tier_counts[tier] += 1
        if dtype:
            dtype_counts[dtype] += 1

        if tier not in ALLOWED_TIERS:
            bad_tier.append((i, tier))
        if dtype not in ALLOWED_DATA_TYPES:
            bad_dtype.append((i, dtype))

        if src == "":
            missing_source.append(i)
        elif "REPLACE_ME" in src.upper():
            replace_me.append(i)

    dup_list = [(k, c) for k, c in dupes.items() if c > 1]
    dup_list.sort(key=lambda x: x[1], reverse=True)

    print("\n[REPORT] Points CSV Preflight")
    print(f"  File: {csv_path}")
    print(f"  Rows (points): {total}")

    print("\n[COUNTS] Tier distribution")
    for t in ("1", "2", "3"):
        print(f"  tier {t}: {tier_counts.get(t, 0)}")

    print("\n[COUNTS] Data types")
    for k, v in sorted(dtype_counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {k}: {v}")

    if bad_tier:
        print(f"\n[WARN] Invalid tier values (showing up to 20): {len(bad_tier)}")
        for rownum, val in bad_tier[:20]:
            print(f"  row {rownum}: tier={val!r} (allowed: 1,2,3)")

    if bad_dtype:
        print(f"\n[WARN] Invalid data_type values (showing up to 20): {len(bad_dtype)}")
        for rownum, val in bad_dtype[:20]:
            print(f"  row {rownum}: data_type={val!r} (allowed: float,int,bool,string,enum)")

    if missing_source:
        print(f"\n[WARN] Missing source_ref: {len(missing_source)} rows (showing up to {args.max_missing})")
        for rownum in missing_source[: args.max_missing]:
            print(f"  row {rownum}")

    if replace_me:
        print(f"\n[INFO] Placeholder source_ref contains REPLACE_ME: {len(replace_me)} rows (showing up to {args.max_missing})")
        for rownum in replace_me[: args.max_missing]:
            print(f"  row {rownum}")

    if dup_list:
        print(f"\n[WARN] Duplicate (asset_id, point_id) keys: {len(dup_list)} (showing up to {args.max_dupes})")
        for (asset_id, point_id), c in dup_list[: args.max_dupes]:
            print(f"  ({asset_id}, {point_id}) appears {c} times")
    else:
        print("\n[OK] No duplicate (asset_id, point_id) keys found.")

    print("\n[OK] Preflight complete.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
