from __future__ import annotations

import hashlib
import hmac
import json

HMAC_KEY = b"cell-platform-demo-hmac-not-a-production-secret"


def sign_envelope(tenant_id: str, tenant_version: int, payload: dict) -> str:
    body = json.dumps(
        {"tenant_id": tenant_id, "tenant_version": tenant_version, "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hmac.new(HMAC_KEY, body, hashlib.sha256).hexdigest()


class TenantTask:
    def apply(self, tenant_id: str, tenant_version: int, payload: dict, signature: str | None):
        expected = sign_envelope(tenant_id, tenant_version, payload)
        if not signature or not hmac.compare_digest(expected, signature):
            raise PermissionError("unsigned or invalid tenant envelope")
        return {"ok": True, "tenant_id": tenant_id}
