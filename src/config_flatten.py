from typing import List
from models import PointDef


def extract_points(cfg: dict) -> List[PointDef]:
    """
    Convert the YAML config into a flat list of PointDef objects.
    Also enforces guardrails (duplicate IDs, tier rules, defaults).
    """
    defaults = cfg["defaults"]
    tiers = defaults["tiers"]

    default_analog_deadband = float(defaults["analog"]["deadband"])

    points: List[PointDef] = []
    seen_ids = set()

    for asset in cfg["assets"]:
        for p in asset["points"]:
            point_id = p["point_id"]

            # 1) Unique point_id rule
            if point_id in seen_ids:
                raise ValueError(f"Duplicate point_id found in config: {point_id}")
            seen_ids.add(point_id)

            # 2) Tier + defaults
            tier = int(p["tier"])
            if tier not in (1, 2, 3):
                raise ValueError(f"Invalid tier for {point_id}: {tier}")

            default_min_publish = int(tiers[str(tier)]["min_publish_seconds"])

            data_type = p["data_type"]
            is_analog = data_type in ("float", "int")

            # 3) Deadband defaulting
            if "deadband" in p:
                deadband = float(p["deadband"])
            else:
                deadband = default_analog_deadband if is_analog else 0.0

            # 4) Min publish defaulting
            min_publish_seconds = int(p.get("min_publish_seconds", default_min_publish))

            # 5) Guardrail: Tier 1 analog MUST have deadband > 0
            if tier == 1 and is_analog and deadband <= 0:
                raise ValueError(f"Tier 1 analog point must have deadband > 0: {point_id}")

            points.append(
                PointDef(
                    point_id=point_id,
                    name=p["name"],
                    point_kind=p["point_kind"],
                    data_type=data_type,
                    unit=p.get("unit"),
                    tier=tier,
                    deadband=deadband,
                    min_publish_seconds=min_publish_seconds,
                    source_ref=p["source_ref"],
                )
            )

    if not points:
        raise ValueError("No points found in config. Add at least one point under assets[].points[].")

    return points
