from __future__ import annotations

import threading
from typing import Any

from .models import (
    AuditEvent,
    BreakGlass,
    Cell,
    IsolationRun,
    Membership,
    Release,
    Tenant,
    utcnow,
)


class Store:
    """In-process source of truth. Tests get a fresh instance via app dependency."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.tenants: dict[str, Tenant] = {}
        self.cells: dict[str, Cell] = {}
        self.releases: dict[str, Release] = {}
        self.memberships: list[Membership] = []
        self.break_glass: dict[str, BreakGlass] = {}
        self.audit: list[AuditEvent] = []
        self.isolation_runs: list[IsolationRun] = []
        self.secrets: dict[str, dict[str, str]] = {}
        self.tenant_dbs: dict[str, dict[str, Any]] = {}
        self.cache: dict[str, Any] = {}
        self.task_envelopes: list[dict[str, Any]] = []
        self.fleet_release = "V7"
        self.artifact_digest = "sha256:demo-v7"
        self.orphans: list[str] = []
        self.seeded_cells = False

    def audit_event(self, action: str, **kwargs: Any) -> None:
        with self._lock:
            self.audit.append(AuditEvent(action=action, **kwargs))

    def touch(self, tenant: Tenant) -> Tenant:
        tenant.updated_at = utcnow()
        self.tenants[tenant.tenant_id] = tenant
        return tenant


STORE = Store()
