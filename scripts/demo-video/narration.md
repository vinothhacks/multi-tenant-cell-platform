# Demo narration (one block per scene — never overlap motion)

## scene-01-problem
Fifty tenants used to mean fifty environments, fifty deployments, fifty configs, and fifty monitoring stacks. Operations scaled as O of N.

## scene-02-target
The target is a control plane that places tenants into cells. Each tenant keeps its own database. Fleet operations become O of waves.

## scene-03-create
Watch the controller reconcile a new tenant from requested through database, schema, secrets, and routing, until the tenant is active.

## scene-04-scale
We seed a synthetic fleet. When CELL-01 hits capacity, placement opens CELL-02 automatically.

## scene-05-move
Acme moves between cells. Copy, validation, quiesce, epoch increment, then routing switch. The registry commit is the cutover.

## scene-06-release
Release V8 is one signed artifact. Canary, then wave one, then the fleet. Not N manual deploys.

## scene-07-break
We take one tenant database down. That tenant becomes degraded. The other tenants stay healthy. Faults stay contained.
