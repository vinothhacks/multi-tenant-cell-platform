# Threat model (demo)

| Scenario | Prevent | Detect | Respond |
|---|---|---|---|
| Request without tenant | Fail closed (I1) | 400 metric | Reject |
| Tenant A → Tenant B DB | Alias + current_database assert (I2) | Isolation run | Block + audit |
| Cross-cell secret read | Path `cells/{cell}/tenants/{id}` (I3) | Invariant I3 | Deny |
| Unsigned Celery task | HMAC envelope (I4) | 401 | DLQ conceptually |
| Registry orphan | I5/I6 | Isolation run | Quarantine |
| Support abuse | Time-limited break-glass (I10) | Audit | Expiry |
| Compromised pod (pooled) | Cell-scoped secrets | Unexpected secret path | Rotate + dedicated SKU |
