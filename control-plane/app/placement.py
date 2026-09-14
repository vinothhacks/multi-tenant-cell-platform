from __future__ import annotations

from .models import Cell, IsolationClass, SizeClass, Tier, new_id
from .store import Store

POOLED_CAPACITY = 8


def ensure_base_cells(store: Store) -> None:
    if store.seeded_cells:
        return
    store.cells["cell-01"] = Cell(
        cell_id="cell-01",
        name="CELL-01",
        kind="pooled",
        capacity=POOLED_CAPACITY,
        cpu=61.0,
        memory=58.0,
        pg_connections=63.0,
        iops=54.0,
        redis=47.0,
        celery=39.0,
    )
    store.cells["cell-02"] = Cell(
        cell_id="cell-02",
        name="CELL-02",
        kind="pooled",
        capacity=POOLED_CAPACITY,
        cpu=49.0,
        memory=44.0,
        pg_connections=41.0,
        iops=38.0,
        redis=33.0,
        celery=28.0,
    )
    store.seeded_cells = True


def _headroom(store: Store, cell: Cell) -> int:
    used = sum(1 for t in store.tenants.values() if t.cell_id == cell.cell_id and t.status.value != "deleted")
    return cell.capacity - used


def place(
    store: Store,
    *,
    isolation: IsolationClass,
    size: SizeClass,
    region: str,
    name: str,
) -> tuple[Tier, Cell]:
    """Placement policy is the decision engine. C/D/E are outputs."""
    ensure_base_cells(store)

    if isolation == IsolationClass.L3:
        cell = Cell(
            cell_id=f"sov-{new_id()[:8]}",
            name=f"SOVEREIGN-{name[:12]}",
            kind="sovereign",
            region=region,
            capacity=1,
        )
        store.cells[cell.cell_id] = cell
        return Tier.SOVEREIGN, cell

    if isolation == IsolationClass.L2 or size in {SizeClass.L, SizeClass.XL}:
        cell = Cell(
            cell_id=f"d-{new_id()[:8]}",
            name=f"D-{name[:16]}",
            kind="dedicated",
            region=region,
            capacity=1,
        )
        store.cells[cell.cell_id] = cell
        return Tier.DEDICATED, cell

    pooled = [c for c in store.cells.values() if c.kind == "pooled"]
    pooled.sort(key=lambda c: _headroom(store, c), reverse=True)
    if pooled and _headroom(store, pooled[0]) > 0:
        return Tier.POOLED, pooled[0]

    n = len(pooled) + 1
    cell = Cell(
        cell_id=f"cell-{n:02d}",
        name=f"CELL-{n:02d}",
        kind="pooled",
        region=region,
        capacity=POOLED_CAPACITY,
    )
    store.cells[cell.cell_id] = cell
    return Tier.POOLED, cell


def cell_utilization(store: Store, cell: Cell) -> dict:
    tenants = [t for t in store.tenants.values() if t.cell_id == cell.cell_id and t.status.value != "deleted"]
    sizes = {"S": 0, "M": 0, "L": 0, "XL": 0}
    for t in tenants:
        sizes[t.size_class.value] += 1
    used = len(tenants)
    pct = 0 if cell.capacity == 0 else round(100 * used / cell.capacity)
    return {
        "tenants": used,
        "capacity": cell.capacity,
        "utilization_pct": pct,
        "size_mix": sizes,
        "headroom": cell.capacity - used,
    }
