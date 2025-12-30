# src/planner.py
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any


@dataclass(frozen=True)
class PlannedPoint:
    asset_id: str
    asset_name: str
    point_id: str
    point_name: str
    data_type: str
    tier: int
    poll_seconds: int
    min_publish_seconds: int
    deadband: float
    source_ref: str


def build_poll_plan(cfg: Dict[str, Any]) -> List[PlannedPoint]:
    defaults = cfg["polling"]["defaults"]
    tiers = defaults["tiers"]

    analog_db = float(defaults["analog"]["deadband"])
    digital_db = float(defaults["digital"]["deadband"])

    plan: List[PlannedPoint] = []

    for asset in cfg["metasys"]["assets"]:
        asset_id = asset["asset_id"]
        asset_name = asset.get("name", asset_id)

        for p in asset["points"]:
            tier = int(p["tier"])
            tier_cfg = tiers[str(tier)]

            poll_seconds = int(tier_cfg["poll_seconds"])
            min_pub = int(p.get(
                "min_publish_seconds",
                tier_cfg["min_publish_seconds"]
            ))

            is_analog = p["data_type"] in ("float", "int")
            deadband = float(p.get(
                "deadband",
                analog_db if is_analog else digital_db
            ))

            plan.append(
                PlannedPoint(
                    asset_id=asset_id,
                    asset_name=asset_name,
                    point_id=p["point_id"],
                    point_name=p.get("name", p["point_id"]),
                    data_type=p["data_type"],
                    tier=tier,
                    poll_seconds=poll_seconds,
                    min_publish_seconds=min_pub,
                    deadband=deadband,
                    source_ref=p["source_ref"],
                )
            )

    plan.sort(key=lambda x: (x.tier, x.asset_id, x.point_id))
    return plan


def summarize_plan(plan: List[PlannedPoint]) -> Tuple[Dict[int, int], int]:
    by_tier: Dict[int, int] = {}
    for p in plan:
        by_tier[p.tier] = by_tier.get(p.tier, 0) + 1
    return by_tier, len(plan)

