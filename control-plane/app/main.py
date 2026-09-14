from __future__ import annotations

import os
import re
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .controller import CrashInjected, offboard, reconcile_provision, resume, suspend
from .dataplane import sign_envelope, verify_envelope
from .identity import add_membership, issue_break_glass
from .isolation import mark_db_down, probe_cross_tenant, run_invariants
from .models import (
    BreakGlassIn,
    ChaosIn,
    IsolationClass,
    IsolationIn,
    LifecycleStatus,
    MoveRequest,
    ReleaseIn,
    SeedIn,
    SizeClass,
    TaskIn,
    Tenant,
    TenantCreate,
    new_id,
)
from .moves import MoveCrashed, advance_move, start_move
from .placement import cell_utilization, ensure_base_cells, place
from .releases import continue_wave, halt, rollback, resume_desired, start_release
from .store import STORE, Store

SLUG_RE = re.compile(r"[^a-z0-9]+")


def get_store() -> Store:
    return STORE


def slugify(name: str) -> str:
    s = SLUG_RE.sub("-", name.lower()).strip("-")
    return s or "tenant"


def tenant_or_404(store: Store, tenant_id: str) -> Tenant:
    t = store.tenants.get(tenant_id)
    if not t:
        raise HTTPException(404, "tenant not found")
    return t


def serialize_tenant(t: Tenant) -> dict:
    duration = None
    if t.provisioned_at:
        duration = round((t.provisioned_at - t.created_at).total_seconds(), 3)
    return {
        **t.model_dump(mode="json"),
        "provisioning_seconds": duration,
        "database": t.database_name,
    }


def create_tenant_record(store: Store, body: TenantCreate) -> Tenant:
    ensure_base_cells(store)
    tenant_id = new_id()
    slug = slugify(body.name)
    existing = {x.slug for x in store.tenants.values()}
    base = slug
    n = 2
    while slug in existing:
        slug = f"{base}-{n}"
        n += 1
    tier, cell = place(
        store,
        isolation=body.isolation,
        size=body.size_class,
        region=body.region,
        name=body.name,
    )
    tenant = Tenant(
        tenant_id=tenant_id,
        name=body.name,
        slug=slug,
        isolation=body.isolation,
        size_class=body.size_class,
        contract=body.contract,
        region=body.region,
        tier=tier,
        cell_id=cell.cell_id,
        database_name=f"db_{slug.replace('-', '_')}",
        crash_after=body.crash_after,
        inject_migration_failure=body.inject_migration_failure,
        schema_version=store.fleet_release,
    )
    store.tenants[tenant_id] = tenant
    add_membership(store, "demo-user", tenant_id, "owner")
    store.audit_event("tenant_requested", tenant_id=tenant_id, cell_id=cell.cell_id)
    return tenant


def fleet_snapshot(store: Store) -> dict:
    ensure_base_cells(store)
    tenants = [t for t in store.tenants.values() if t.status != LifecycleStatus.DELETED]
    pooled = sum(1 for t in tenants if t.tier.value == "pooled")
    dedicated = sum(1 for t in tenants if t.tier.value == "dedicated")
    sovereign = sum(1 for t in tenants if t.tier.value == "sovereign")
    healthy = sum(1 for t in tenants if t.health.value == "healthy")
    versions = {t.schema_version for t in tenants}
    skew = max(0, len(versions) - 1)
    onboard = [
        (t.provisioned_at - t.created_at).total_seconds()
        for t in tenants
        if t.provisioned_at
    ]
    return {
        "total_tenants": len(tenants),
        "pooled": pooled,
        "dedicated": dedicated,
        "sovereign": sovereign,
        "cells": len(store.cells),
        "healthy": f"{healthy}/{len(tenants)}" if tenants else "0/0",
        "healthy_count": healthy,
        "onboarding_seconds_p50": sorted(onboard)[len(onboard) // 2] if onboard else 0,
        "fleet_release": store.fleet_release,
        "version_skew": skew,
        "artifact_digest": store.artifact_digest,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_base_cells(STORE)
    yield


def create_app(store: Store | None = None) -> FastAPI:
    app = FastAPI(title="Cell Platform Control Plane", version="0.1.0", lifespan=lifespan)
    origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins] + ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def dep() -> Store:
        return store or get_store()

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "control-plane"}

    @app.get("/v1/fleet")
    def fleet(st: Store = Depends(dep)):
        snap = fleet_snapshot(st)
        tenants = [
            serialize_tenant(t)
            for t in st.tenants.values()
            if t.status != LifecycleStatus.DELETED
        ]
        tenants.sort(key=lambda x: x["created_at"])
        return {**snap, "tenants": tenants}

    @app.get("/v1/tenants")
    def list_tenants(st: Store = Depends(dep)):
        return [serialize_tenant(t) for t in st.tenants.values()]

    @app.post("/v1/tenants", status_code=201)
    def create_tenant(payload: TenantCreate, st: Store = Depends(dep)):
        tenant = create_tenant_record(st, payload)
        try:
            reconcile_provision(st, tenant)
        except CrashInjected:
            pass
        return serialize_tenant(tenant)

    @app.get("/v1/tenants/{tenant_id}")
    def get_tenant(tenant_id: str, st: Store = Depends(dep)):
        t = tenant_or_404(st, tenant_id)
        cell = st.cells.get(t.cell_id)
        return {
            **serialize_tenant(t),
            "components": {
                "api": "healthy" if not t.db_unavailable else "down",
                "celery": "healthy" if t.status != LifecycleStatus.SUSPENDED else "paused",
                "redis": "healthy",
                "postgresql": "down" if t.db_unavailable else "healthy",
            },
            "cell": cell.model_dump(mode="json") if cell else None,
        }

    @app.post("/v1/tenants/{tenant_id}/reconcile")
    def reconcile(tenant_id: str, st: Store = Depends(dep)):
        t = tenant_or_404(st, tenant_id)
        t.crash_after = None
        try:
            reconcile_provision(st, t)
        except CrashInjected:
            pass
        return serialize_tenant(t)

    @app.post("/v1/tenants/{tenant_id}/suspend")
    def suspend_tenant(tenant_id: str, st: Store = Depends(dep)):
        t = tenant_or_404(st, tenant_id)
        return serialize_tenant(suspend(st, t))

    @app.post("/v1/tenants/{tenant_id}/resume")
    def resume_tenant(tenant_id: str, st: Store = Depends(dep)):
        t = tenant_or_404(st, tenant_id)
        try:
            return serialize_tenant(resume(st, t))
        except ValueError as e:
            raise HTTPException(400, str(e)) from e

    @app.post("/v1/tenants/{tenant_id}/delete")
    def delete_tenant(tenant_id: str, st: Store = Depends(dep)):
        t = tenant_or_404(st, tenant_id)
        return serialize_tenant(offboard(st, t))

    @app.post("/v1/tenants/{tenant_id}/move")
    def move_tenant(tenant_id: str, payload: MoveRequest, st: Store = Depends(dep)):
        t = tenant_or_404(st, tenant_id)
        target = payload.target_cell_id
        if not target:
            pooled = [c.cell_id for c in st.cells.values() if c.kind == "pooled" and c.cell_id != t.cell_id]
            if not pooled:
                raise HTTPException(400, "no target cell")
            target = pooled[0]
        try:
            start_move(st, t, target, payload.reason)
            t = advance_move(
                st,
                t,
                abort_before_commit=payload.abort_before_commit,
                crash_before_commit=payload.crash_before_commit,
            )
        except MoveCrashed:
            return serialize_tenant(t)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        return serialize_tenant(t)

    @app.get("/v1/cells")
    def list_cells(st: Store = Depends(dep)):
        ensure_base_cells(st)
        out = []
        for c in st.cells.values():
            util = cell_utilization(st, c)
            out.append({**c.model_dump(mode="json"), **util})
        return out

    @app.get("/v1/cells/{cell_id}")
    def get_cell(cell_id: str, st: Store = Depends(dep)):
        c = st.cells.get(cell_id)
        if not c:
            raise HTTPException(404, "cell not found")
        tenants = [serialize_tenant(t) for t in st.tenants.values() if t.cell_id == cell_id]
        return {**c.model_dump(mode="json"), **cell_utilization(st, c), "tenants": tenants}

    @app.get("/v1/releases")
    def list_releases(st: Store = Depends(dep)):
        return [r.model_dump(mode="json") for r in st.releases.values()]

    @app.post("/v1/releases")
    def create_release(payload: ReleaseIn, st: Store = Depends(dep)):
        rel = start_release(st, payload.version)
        return _release_view(st, rel)

    @app.post("/v1/releases/{release_id}/continue")
    def continue_release(release_id: str, st: Store = Depends(dep)):
        rel = st.releases.get(release_id)
        if not rel:
            raise HTTPException(404, "release not found")
        try:
            continue_wave(st, rel)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        return _release_view(st, rel)

    @app.post("/v1/releases/{release_id}/halt")
    def halt_release(release_id: str, st: Store = Depends(dep)):
        rel = st.releases.get(release_id)
        if not rel:
            raise HTTPException(404, "release not found")
        halt(st, rel)
        return _release_view(st, rel)

    @app.post("/v1/releases/{release_id}/rollback")
    def rollback_release(release_id: str, st: Store = Depends(dep)):
        rel = st.releases.get(release_id)
        if not rel:
            raise HTTPException(404, "release not found")
        rollback(st, rel, "V7")
        return _release_view(st, rel)

    @app.post("/v1/releases/{release_id}/resume")
    def resume_release(release_id: str, st: Store = Depends(dep)):
        rel = st.releases.get(release_id)
        if not rel:
            raise HTTPException(404, "release not found")
        resume_desired(st, rel)
        return _release_view(st, rel)

    def _release_view(st: Store, rel):
        tenants = [t for t in st.tenants.values() if t.status != LifecycleStatus.DELETED]
        on_rel = sum(1 for t in tenants if t.schema_version == rel.version)
        return {
            **rel.model_dump(mode="json"),
            "schema": {"on_release": on_rel, "total": len(tenants)},
            "cells": [
                {
                    "cell_id": c.cell_id,
                    "release": c.release,
                    "desired": c.desired_release,
                    "state": rel.cell_state.get(c.cell_id, "waiting"),
                }
                for c in st.cells.values()
            ],
        }

    @app.post("/v1/isolation/run")
    def isolation_run(payload: IsolationIn, st: Store = Depends(dep)):
        run = run_invariants(st, payload.tenant_a, payload.tenant_b)
        extra = {}
        if payload.tenant_a and payload.tenant_b:
            extra["probe"] = {
                "attempt": f"{payload.tenant_a} -> {payload.tenant_b} DB",
                "blocked": run.blocked_cross_tenant,
                "reason": run.reason,
            }
        return {**run.model_dump(mode="json"), **extra}

    @app.post("/v1/chaos/db-down")
    def chaos_db(payload: ChaosIn, st: Store = Depends(dep)):
        tenant_or_404(st, payload.tenant_id)
        mark_db_down(st, payload.tenant_id)
        others = [
            t
            for t in st.tenants.values()
            if t.tenant_id != payload.tenant_id and t.status == LifecycleStatus.ACTIVE
        ]
        return {
            "degraded": payload.tenant_id,
            "others_healthy": all(t.health.value == "healthy" for t in others),
            "others": len(others),
        }

    @app.post("/v1/synthetic/seed")
    def seed(payload: SeedIn, st: Store = Depends(dep)):
        created = []
        for i in range(payload.count):
            t = create_tenant_record(
                st,
                TenantCreate(name=f"{payload.prefix}-{i+1:02d}", isolation=IsolationClass.L1, size_class=SizeClass.S),
            )
            reconcile_provision(st, t)
            created.append(t.tenant_id)
        return {"created": created, "fleet": fleet_snapshot(st)}

    @app.get("/v1/economics")
    def economics():
        return {
            "label": "Simulation / illustrative model — not production savings",
            "rows": [
                {"n": 20, "silo": 9600, "pooled": 5660},
                {"n": 100, "silo": 48000, "pooled": 10050},
                {"n": 500, "silo": 240000, "pooled": 32750},
                {"n": 1000, "silo": 480000, "pooled": 61000},
            ],
        }

    @app.get("/v1/observability")
    def observability(st: Store = Depends(dep)):
        cells = []
        for c in st.cells.values():
            util = cell_utilization(st, c)
            cells.append({"cell_id": c.cell_id, "utilization": util["utilization_pct"], **util})
        return {
            "api_availability": 99.96,
            "p99_latency_ms": 182,
            "queue_start_p95_s": 1.4,
            "pg_utilization": 62,
            "redis_utilization": 51,
            "cells": cells,
        }

    @app.get("/v1/audit")
    def audit(st: Store = Depends(dep)):
        return [e.model_dump(mode="json") for e in st.audit[-200:]]

    @app.post("/v1/identity/break-glass")
    def bg(payload: BreakGlassIn, st: Store = Depends(dep)):
        tenant_or_404(st, payload.tenant_id)
        ticket = issue_break_glass(st, payload.tenant_id, payload.actor, payload.reason)
        return ticket.model_dump(mode="json")

    @app.get("/dp/health")
    def dp_health(
        x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
        st: Store = Depends(dep),
    ):
        if not x_tenant_id:
            raise HTTPException(400, "tenant identity required")
        t = tenant_or_404(st, x_tenant_id)
        if t.status in {LifecycleStatus.SUSPENDED, LifecycleStatus.DELETED}:
            raise HTTPException(403, "tenant not active")
        if t.db_unavailable:
            raise HTTPException(503, "tenant database unavailable")
        db = st.tenant_dbs.get(t.tenant_id)
        if not db:
            raise HTTPException(503, "database missing")
        if db["database"] != t.database_name:
            raise HTTPException(500, "current_database != expected_database")
        return {
            "tenant_id": t.tenant_id,
            "database": db["database"],
            "cell_id": t.cell_id,
            "rows": db["rows"],
        }

    @app.post("/dp/tasks")
    def enqueue_task(payload: TaskIn, st: Store = Depends(dep)):
        t = tenant_or_404(st, payload.tenant_id)
        envelope = {
            "tenant_id": t.tenant_id,
            "tenant_version": t.tenant_version,
            "payload": payload.payload,
        }
        sig = payload.signature or (None if payload.unsigned else sign_envelope(envelope))
        if not sig or not verify_envelope(envelope, sig):
            raise HTTPException(401, "unsigned or invalid tenant envelope")
        st.task_envelopes.append({**envelope, "signature": sig})
        return {"accepted": True}

    return app


app = create_app()
