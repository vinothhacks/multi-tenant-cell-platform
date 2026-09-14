from __future__ import annotations

import hashlib

from .models import Health, LifecycleStatus, Release, Tenant, new_id
from .store import Store

WAVES = ["canary", "wave1", "fleet"]


def _pooled_cells(store: Store) -> list[str]:
    cells = [c for c in store.cells.values() if c.kind == "pooled"]
    cells.sort(key=lambda c: c.cell_id)
    return [c.cell_id for c in cells]


def _wave_members(store: Store, wave: str) -> list[str]:
    ids = _pooled_cells(store)
    if not ids:
        return []
    if wave == "canary":
        return ids[:1]
    if wave == "wave1":
        n = max(1, len(ids) // 4)
        return ids[1 : 1 + n] if len(ids) > 1 else []
    assigned = set(_wave_members(store, "canary") + _wave_members(store, "wave1"))
    rest = [i for i in ids if i not in assigned]
    dedicated = [c.cell_id for c in store.cells.values() if c.kind != "pooled"]
    return rest + dedicated


def start_release(store: Store, version: str) -> Release:
    digest = "sha256:" + hashlib.sha256(version.encode()).hexdigest()[:16]
    rel = Release(
        release_id=new_id(),
        version=version,
        digest=digest,
        cell_state={cid: "waiting" for cid in store.cells},
    )
    store.releases[rel.release_id] = rel
    store.artifact_digest = digest
    store.audit_event("release_started", detail={"version": version, "digest": digest})
    _apply_wave(store, rel, "canary")
    return rel


def _apply_wave(store: Store, rel: Release, wave: str) -> None:
    if rel.halted:
        return
    rel.wave = wave
    for cell_id in _wave_members(store, wave):
        cell = store.cells[cell_id]
        cell.desired_release = rel.version
        failed = _migrate_cell(store, rel, cell_id)
        if failed and _systemic(store, cell_id):
            rel.halted = True
            rel.status = "halted"
            store.audit_event("release_halted", cell_id=cell_id, detail={"wave": wave})
            return
        cell.release = rel.version
        rel.cell_state[cell_id] = "healthy"
    if wave == "fleet" and not rel.halted:
        rel.status = "complete"
        store.fleet_release = rel.version


def _migrate_cell(store: Store, rel: Release, cell_id: str) -> int:
    failed = 0
    tenants = [t for t in store.tenants.values() if t.cell_id == cell_id and t.status != LifecycleStatus.DELETED]
    for t in tenants:
        if t.inject_migration_failure:
            t.status = LifecycleStatus.DEGRADED
            t.health = Health.DEGRADED
            failed += 1
            store.audit_event("migration_failed", tenant_id=t.tenant_id, cell_id=cell_id)
            continue
        t.schema_version = rel.version
        if t.status == LifecycleStatus.DEGRADED and not t.db_unavailable:
            t.status = LifecycleStatus.ACTIVE
            t.health = Health.HEALTHY
        store.touch(t)
    return failed


def _systemic(store: Store, cell_id: str) -> bool:
    tenants = [t for t in store.tenants.values() if t.cell_id == cell_id and t.status != LifecycleStatus.DELETED]
    if not tenants:
        return False
    degraded = sum(1 for t in tenants if t.status == LifecycleStatus.DEGRADED)
    return degraded / len(tenants) > 0.02 and degraded >= 2


def continue_wave(store: Store, rel: Release) -> Release:
    if rel.halted:
        raise ValueError("halted")
    idx = WAVES.index(rel.wave) if rel.wave in WAVES else 0
    if idx >= len(WAVES) - 1:
        rel.status = "complete"
        return rel
    _apply_wave(store, rel, WAVES[idx + 1])
    return rel


def halt(store: Store, rel: Release) -> Release:
    rel.halted = True
    rel.status = "halted"
    store.audit_event("release_halted_manual", detail={"release": rel.version})
    return rel


def rollback(store: Store, rel: Release, to_version: str) -> Release:
    for cell in store.cells.values():
        if rel.cell_state.get(cell.cell_id) == "healthy":
            cell.release = to_version
            rel.cell_state[cell.cell_id] = "rolled_back"
    rel.status = "rolled_back"
    rel.halted = True
    store.fleet_release = to_version
    return rel


def resume_desired(store: Store, rel: Release) -> Release:
    """Orchestrator crash recovery: desired vs actual, do not restart blindly."""
    rel.halted = False
    if rel.status == "complete":
        return rel
    wave = rel.wave if rel.wave in WAVES else "canary"
    for cell_id in _wave_members(store, wave):
        cell = store.cells[cell_id]
        if cell.release != rel.version:
            _migrate_cell(store, rel, cell_id)
            cell.release = rel.version
            rel.cell_state[cell_id] = "healthy"
    return rel
