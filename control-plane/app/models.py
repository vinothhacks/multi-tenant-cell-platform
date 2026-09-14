from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid4())


class IsolationClass(str, Enum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class SizeClass(str, Enum):
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"


class Tier(str, Enum):
    POOLED = "pooled"
    DEDICATED = "dedicated"
    SOVEREIGN = "sovereign"


class Health(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


class LifecycleStatus(str, Enum):
    REQUESTED = "requested"
    PROVISIONING = "provisioning"
    DATABASE_READY = "database_ready"
    SCHEMA_READY = "schema_ready"
    SECRETS_READY = "secrets_ready"
    ROUTING_READY = "routing_ready"
    ACTIVE = "active"
    FAILED = "failed"
    FAILED_TERMINAL = "failed_terminal"
    SUSPENDED = "suspended"
    RETENTION_HOLD = "retention_hold"
    DELETING = "deleting"
    DELETED = "deleted"
    MIGRATING = "migrating"
    MIGRATING_SETUP = "migrating_setup"
    MIGRATING_CATCHUP = "migrating_catchup"
    MIGRATING_QUIESCE = "migrating_quiesce"
    MIGRATING_VALIDATE = "migrating_validate"
    CUTOVER = "cutover"
    DEGRADED = "degraded"


PROVISION_STEPS = [
    LifecycleStatus.PROVISIONING,
    LifecycleStatus.DATABASE_READY,
    LifecycleStatus.SCHEMA_READY,
    LifecycleStatus.SECRETS_READY,
    LifecycleStatus.ROUTING_READY,
    LifecycleStatus.ACTIVE,
]

MOVE_GATES = [
    "initial_copy",
    "replication",
    "catch_up",
    "lag_zero",
    "transactions_zero",
    "sequences_synced",
    "validation",
    "health_check",
    "epoch_increment",
    "routing_switched",
]


class Cell(BaseModel):
    cell_id: str
    name: str
    kind: str = "pooled"
    region: str = "Chennai"
    capacity: int = 8
    release: str = "V7"
    desired_release: str = "V7"
    health: Health = Health.HEALTHY
    cpu: float = 42.0
    memory: float = 38.0
    pg_connections: float = 31.0
    iops: float = 28.0
    redis: float = 22.0
    celery: float = 18.0
    created_at: datetime = Field(default_factory=utcnow)


class Tenant(BaseModel):
    tenant_id: str
    name: str
    slug: str
    isolation: IsolationClass
    size_class: SizeClass
    contract: str = "standard"
    region: str = "Chennai"
    tier: Tier
    cell_id: str
    database_name: str
    schema_version: str = "V7"
    tenant_version: int = 1
    secret_version: int = 1
    flags: dict[str, Any] = Field(default_factory=dict)
    status: LifecycleStatus = LifecycleStatus.REQUESTED
    lifecycle_step: str = "requested"
    completed_steps: list[str] = Field(default_factory=list)
    health: Health = Health.UNKNOWN
    crash_after: str | None = None
    inject_migration_failure: bool = False
    db_unavailable: bool = False
    legal_hold: bool = False
    source_cell_id: str | None = None
    move_target_cell_id: str | None = None
    move_reason: str | None = None
    move_gates: dict[str, bool] = Field(default_factory=dict)
    move_committed: bool = False
    provisioned_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Membership(BaseModel):
    user_id: str
    tenant_id: str
    role: str = "member"
    status: str = "active"


class BreakGlass(BaseModel):
    ticket_id: str
    tenant_id: str
    actor: str
    reason: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=utcnow)
    revoked: bool = False


class Release(BaseModel):
    release_id: str
    version: str
    digest: str
    sbom: bool = True
    scanned: bool = True
    signed: bool = True
    status: str = "in_progress"
    wave: str = "canary"
    halted: bool = False
    error_budget: float = 82.0
    cell_state: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=new_id)
    at: datetime = Field(default_factory=utcnow)
    actor: str = "control-plane"
    action: str
    tenant_id: str | None = None
    cell_id: str | None = None
    detail: dict[str, Any] = Field(default_factory=dict)


class IsolationRun(BaseModel):
    run_id: str
    at: datetime = Field(default_factory=utcnow)
    results: dict[str, str]
    blocked_cross_tenant: bool = False
    reason: str | None = None


class TenantCreate(BaseModel):
    name: str
    isolation: IsolationClass = IsolationClass.L1
    size_class: SizeClass = SizeClass.S
    region: str = "Chennai"
    contract: str = "standard"
    crash_after: str | None = None
    inject_migration_failure: bool = False


class MoveRequest(BaseModel):
    target_cell_id: str | None = None
    reason: str = "cell capacity / noisy neighbour"
    abort_before_commit: bool = False
    crash_before_commit: bool = False


class ReleaseIn(BaseModel):
    version: str = "V8"


class IsolationIn(BaseModel):
    tenant_a: str | None = None
    tenant_b: str | None = None


class ChaosIn(BaseModel):
    tenant_id: str


class SeedIn(BaseModel):
    count: int = 20
    prefix: str = "tenant"


class BreakGlassIn(BaseModel):
    tenant_id: str
    actor: str = "sre"
    reason: str


class TaskIn(BaseModel):
    tenant_id: str
    payload: dict = {}
    signature: str | None = None
    unsigned: bool = False
