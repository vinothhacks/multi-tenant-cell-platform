# Runbooks

## Tenant stuck in provisioning
POST `/v1/tenants/{id}/reconcile`. Controller resumes from `completed_steps`.

## Migration degraded
Tenant `schema_status`/`status=degraded`. Fix data, clear `inject_migration_failure`, re-run wave. Do not halt the fleet for a single tenant.

## Move rollback before commit
`abort_before_commit=true` or crash before registry write. Source cell remains authoritative.

## Registry unavailable
Edge/UI should keep last fleet snapshot. This demo serves from process memory; production uses HA Postgres + stale-on-error cache.

## Chaos: tenant DB down
POST `/v1/chaos/db-down`. Expect only that tenant `degraded`.
