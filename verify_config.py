import argparse
import sys
from collections import Counter
from typing import Any, Dict, List, Tuple

import requests
import yaml


def get_json(url: str, timeout: int = 30) -> Dict[str, Any]:
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def post_json(url: str, payload=None, timeout: int = 30) -> Dict[str, Any]:
    r = requests.post(url, json=payload or {}, timeout=timeout)
    r.raise_for_status()
    return r.json()


def normalize_config_obj(cfg: Any) -> Dict[str, Any]:
    if isinstance(cfg, dict) and "config_json" in cfg and isinstance(cfg["config_json"], dict):
        return cfg["config_json"]
    if isinstance(cfg, dict):
        return cfg
    return {}


def extract_yaml_text(yaml_out: Dict[str, Any]) -> str:
    return (
        (yaml_out.get("yaml_text") or "")
        or (yaml_out.get("yaml") or "")
        or (yaml_out.get("text") or "")
    ).strip()


def tier_summary(tiers: List[Dict[str, Any]]) -> List[Tuple[str, int, int]]:
    out = []
    for t in tiers:
        name = str(t.get("name") or "")
        interval = int(t.get("interval_s") or 0)
        pts = t.get("points") or []
        out.append((name, interval, len(pts)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify connector config JSON ↔ generated YAML consistency")
    ap.add_argument("--base", default="http://localhost:8081/api/v1", help="Connector API base (default: %(default)s)")
    ap.add_argument("--project", required=True, help="Project ID (e.g. csudh-pilot-central-plant)")
    ap.add_argument("--timeout", type=int, default=30, help="HTTP timeout seconds (default: %(default)s)")
    ap.add_argument("--max-duplicates-print", type=int, default=10, help="Max duplicate points to print")
    ap.add_argument("--max-spaces-print", type=int, default=10, help="Max spaced points to print")

    args = ap.parse_args()

    base = args.base.rstrip("/")
    project = args.project.strip()

    if not project:
        print("❌ project is required", file=sys.stderr)
        return 2

    cfg_url = f"{base}/projects/{project}/connector/config"
    gen_url = f"{base}/projects/{project}/connector/generate-yaml"

    print(f"🔎 Base:    {base}")
    print(f"🔎 Project: {project}")
    print(f"➡️  GET  {cfg_url}")
    print(f"➡️  POST {gen_url} (dry_run=true)")
    print("")

    try:
        cfg_raw = get_json(cfg_url, timeout=args.timeout)
        yaml_out = post_json(gen_url, payload={"dry_run": True}, timeout=args.timeout)
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection failed: {e}", file=sys.stderr)
        print("   Tip: ensure docker compose is up and the connector port is reachable.", file=sys.stderr)
        return 10
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP error: {e}", file=sys.stderr)
        return 11
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 12

    cfg_obj = normalize_config_obj(cfg_raw)
    yaml_text = extract_yaml_text(yaml_out)

    if not yaml_text:
        print("❌ generate-yaml response did not include yaml_text/yaml/text", file=sys.stderr)
        return 20

    try:
        doc = yaml.safe_load(yaml_text) or {}
    except Exception as e:
        print(f"❌ YAML parse failed: {e}", file=sys.stderr)
        return 21

    # Support either top-level 'connector' or full doc
    json_connector = (cfg_obj.get("connector") or {}) if isinstance(cfg_obj, dict) else {}
    yaml_connector = (doc.get("connector") or {}) if isinstance(doc, dict) else {}

    json_tiers = (json_connector.get("polling") or {}).get("tiers") or []
    yaml_tiers = (yaml_connector.get("polling") or {}).get("tiers") or []

    if not isinstance(json_tiers, list) or not isinstance(yaml_tiers, list):
        print("❌ polling.tiers missing or not a list in JSON or YAML", file=sys.stderr)
        return 30

    print("📌 JSON tiers:", tier_summary(json_tiers))
    print("📌 YAML tiers:", tier_summary(yaml_tiers))
    print("")

    if len(json_tiers) != len(yaml_tiers):
        print(f"❌ Tier count mismatch: JSON={len(json_tiers)} YAML={len(yaml_tiers)}", file=sys.stderr)
        return 40

    for jt, yt in zip(json_tiers, yaml_tiers):
        jn = jt.get("name")
        yn = yt.get("name")
        if jn != yn:
            print(f"❌ Tier name mismatch: {jn} vs {yn}", file=sys.stderr)
            return 41

        ji = int(jt.get("interval_s") or 0)
        yi = int(yt.get("interval_s") or 0)
        if ji != yi:
            print(f"❌ Interval mismatch in {jn}: {ji} vs {yi}", file=sys.stderr)
            return 42

        jp = jt.get("points") or []
        yp = yt.get("points") or []
        if len(jp) != len(yp):
            print(f"❌ Point count mismatch in {jn}: {len(jp)} vs {len(yp)}", file=sys.stderr)
            return 43

    all_points: List[str] = []
    for t in yaml_tiers:
        pts = t.get("points") or []
        all_points.extend([str(p) for p in pts])

    dupes = [p for p, c in Counter(all_points).items() if c > 1]
    spaced = [p for p in all_points if " " in p]

    print(f"✅ YAML total points: {len(all_points)}")
    print(f"✅ Duplicate points: {len(dupes)}")
    if dupes:
        print("   Sample dupes:", dupes[: args.max_duplicates_print])

    print(f"✅ Points containing spaces: {len(spaced)}")
    if spaced:
        print("   Sample spaced:", spaced[: args.max_spaces_print])

    print("")
    print("🎉 PASS: JSON and YAML tier structure matches.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())