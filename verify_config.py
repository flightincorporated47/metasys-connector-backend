import requests
import yaml
from collections import Counter

BASE = "http://127.0.0.1:8787/api/v1"
PROJECT = "csudh-pilot-central-plant"

def get_json(url: str):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

def post_json(url: str, payload=None):
    r = requests.post(url, json=payload or {}, timeout=30)
    r.raise_for_status()
    return r.json()

cfg = get_json(f"{BASE}/projects/{PROJECT}/connector/config")
yaml_out = post_json(f"{BASE}/projects/{PROJECT}/connector/generate-yaml", payload={"dry_run": True})

# Your API might return config under different keys, so we normalize
cfg_obj = cfg.get("config_json") if isinstance(cfg, dict) and "config_json" in cfg else cfg
cfg_connector = cfg_obj.get("connector") if isinstance(cfg_obj, dict) else None

yaml_text = (
    yaml_out.get("yaml_text")
    or yaml_out.get("yaml")
    or yaml_out.get("text")
    or ""
)

if not yaml_text.strip():
    raise SystemExit("❌ generate-yaml response did not include yaml_text/yaml/text")

doc = yaml.safe_load(yaml_text) or {}

json_tiers = (cfg_connector or {}).get("polling", {}).get("tiers", [])
yaml_tiers = (doc.get("connector") or {}).get("polling", {}).get("tiers", [])

print("JSON tiers:", [(t.get("name"), t.get("interval_s"), len(t.get("points", []))) for t in json_tiers])
print("YAML tiers:", [(t.get("name"), t.get("interval_s"), len(t.get("points", []))) for t in yaml_tiers])

if len(json_tiers) != len(yaml_tiers):
    raise SystemExit(f"❌ Tier count mismatch: JSON={len(json_tiers)} YAML={len(yaml_tiers)}")

for jt, yt in zip(json_tiers, yaml_tiers):
    if jt.get("name") != yt.get("name"):
        raise SystemExit(f"❌ Tier name mismatch: {jt.get('name')} vs {yt.get('name')}")
    if int(jt.get("interval_s")) != int(yt.get("interval_s")):
        raise SystemExit(f"❌ Interval mismatch in {jt.get('name')}: {jt.get('interval_s')} vs {yt.get('interval_s')}")
    if len(jt.get("points", [])) != len(yt.get("points", [])):
        raise SystemExit(
            f"❌ Point count mismatch in {jt.get('name')}: "
            f"{len(jt.get('points', []))} vs {len(yt.get('points', []))}"
        )

all_points = []
for t in yaml_tiers:
    all_points.extend(t.get("points", []))

dupes = [p for p, c in Counter(all_points).items() if c > 1]
space_points = [p for p in all_points if " " in p]

print(f"Total points in YAML: {len(all_points)}")
print(f"Duplicate points: {len(dupes)}")
if dupes:
    print("Sample dupes:", dupes[:10])

print(f"Points containing spaces: {len(space_points)}")
if space_points:
    print("Sample spaced points:", space_points[:10])

print("✅ JSON and YAML tier structure matches.")
