# Multi-Tenant Cell Platform — From O(N) Operations to O(Waves)

**Public repo:** https://github.com/vinothhacks/multi-tenant-cell-platform

```text
BEFORE                         AFTER
Tenant A → Stack A                        Control Plane
Tenant B → Stack B                              │
Tenant C → Stack C                     ┌────────┼────────┐
...                                    ↓        ↓        ↓
Tenant N → Stack N                   Cell 1   Cell 2   Cell 3
Operations = O(N)                    N DBs    N DBs    N DBs
                                   Operations = O(waves)
```

This is an **internal architecture control plane**, not a customer SaaS app. The UI proves that tenant registry, placement, provisioning, isolation, movement, releases, and fault containment actually run.

## Quick start (local)

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m uvicorn app.main:app --app-dir control-plane --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 — the console talks to http://localhost:8000.

## What is implemented

| Area | Proof |
|---|---|
| Placement policy | L1/S → pooled, L2 or XL → dedicated, L3 → sovereign |
| Lifecycle | `requested → … → active`, suspend, tombstone delete |
| Cells | Capacity 8; overflow opens CELL-02 |
| Tenant move | Dump/restore copy + cutover commit; abort keeps source |
| Releases | Canary → wave 1 → fleet; one bad tenant → `degraded` |
| Isolation I1–I10 | `/v1/isolation/run` plus Django connection manager |
| Chaos | One tenant DB down; others stay healthy |

Tenant move on managed hosting uses **validated dump/restore**, not logical replication. The UI says so.

## Layout

```text
control-plane/   FastAPI registry, controller, placement, releases
data-plane/      Django tenant middleware + connection manager
frontend/        Next.js control-plane console (6 screens)
infrastructure/  docker-compose + Render Blueprint
tests/           phase-gated pytest
docs/            architecture, ADRs, threat model, phase reports
scripts/demo-video/
```

## Demo story (7 minutes)

1. Problem: N silos  
2. Target: control plane → cells → tenant DBs  
3. Create tenant → state machine to `active`  
4. Seed 20 tenants → CELL-02 receives overflow  
5. Move Acme between cells (epoch++)  
6. Release V7 → V8 by waves  
7. Break one tenant; the rest stay healthy  

## Secrets

Copy `.env.example` to `.env`. Never commit `OPENROUTER_API_KEY`. Video generation is local-only (Phase 10).

## Docs

- [Architecture](docs/architecture.md)
- [Decisions](docs/decisions.md)
- [Threat model](docs/threat-model.md)
- [Runbooks](docs/runbooks.md)
- [Phase reports](docs/phases/)
