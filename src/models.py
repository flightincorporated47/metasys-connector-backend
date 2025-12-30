from dataclasses import dataclass
from typing import Optional, Any


@dataclass(frozen=True)
class PointDef:
    """
    Definition of a point from config (normalized into a simple structure).
    """
    point_id: str
    name: str
    point_kind: str          # sensor|status|setpoint|command|alarm|runtime|totalizer
    data_type: str           # float|int|bool|string|enum
    unit: Optional[str]
    tier: int                # 1|2|3
    deadband: float
    min_publish_seconds: int
    source_ref: str


@dataclass(frozen=True)
class ResolvedHandle:
    """
    A resolved reference to a Metasys object/attribute.
    Populated by the resolver from source_ref.
    """
    point_id: str
    source_ref: str
    object_id: Optional[str] = None
    path: Optional[str] = None
    attribute: Optional[str] = None


@dataclass
class ReadResult:
    """
    Raw-ish result returned by the Metasys client before normalization.
    """
    point_id: str
    ok: bool
    source_ts: str
    value_raw: Optional[str] = None
    status_raw: Optional[str] = None
    reliability_raw: Optional[str] = None
    error_class: Optional[str] = None     # AUTH|NETWORK|SERVER|REQUEST|DATA
    error_message: Optional[str] = None


@dataclass
class NormalizedPoint:
    """
    Normalized data we send to the app in delta batches.
    Matches the delta-batch.v1 point fields.
    """
    point_id: str
    ts: str
    v: Any
    q: str                   # good|bad|uncertain|offline
    s: str                   # normal|alarm|fault|overridden|out_of_service
    rs: Optional[str] = None
