# Demo narration (one block per scene — never overlap motion)

## scene-01-problem
Fifty tenants used to mean fifty environments, fifty deployments, and fifty monitoring stacks. Operations scaled as O of N. This console is the control plane, not a customer product.

## scene-02-hosting
The website you are watching is a Next.js console. In production it is served from Vercel. Every click becomes JSON to a FastAPI control plane on Render. GitHub main is the single source that updates both.

## scene-03-target
The target topology is simple. A registry places each tenant into a cell. Each tenant keeps its own database. Fleet work becomes O of waves, not O of N.

## scene-04-create
Watch the controller reconcile a new tenant. Requested, provisioning, database, schema, secrets, routing, then active. Every step is idempotent and resumable.

## scene-05-scale
We seed a synthetic fleet of twenty tenants. Pooled cell capacity is eight. When CELL-01 and CELL-02 fill, placement opens the next cell automatically.

## scene-06-move
A tenant moves between cells with validated dump and restore, then a registry commit. Copy, validation, epoch increment, routing switch. The source stays authoritative until cutover completes.

## scene-07-release
Release V8 is one signed artifact. Canary the first cell, then continue the wave. Never N manual deploys.

## scene-08-break
We take one tenant database down. That tenant becomes degraded. The other tenants stay healthy. Faults stay inside the partition.
