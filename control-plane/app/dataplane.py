from __future__ import annotations

import copy
import hashlib
import hmac
import json
from pathlib import Path

from .models import Tenant
from .store import Store

HMAC_KEY = b"cell-platform-demo-hmac-not-a-production-secret"


def db_name(tenant: Tenant) -> str:
    return tenant.database_name


def secret_path(cell_id: str, tenant_id: str) -> str:
    return f"cells/{cell_id}/tenants/{tenant_id}/db"


def create_tenant_db(store: Store, tenant: Tenant) -> None:
    store.tenant_dbs[tenant.tenant_id] = {
        "database": tenant.database_name,
        "cell_id": tenant.cell_id,
        "rows": [{"id": 1, "note": f"hello {tenant.slug}"}],
        "schema_version": tenant.schema_version,
        "sequences": {"id": 1},
        "available": True,
    }
    store.secrets[secret_path(tenant.cell_id, tenant.tenant_id)] = {
        "role": f"role_{tenant.slug}",
        "database": tenant.database_name,
        "cell_id": tenant.cell_id,
        "secret_version": str(tenant.secret_version),
    }


def drop_tenant_db(store: Store, tenant: Tenant) -> None:
    store.tenant_dbs.pop(tenant.tenant_id, None)
    store.secrets.pop(secret_path(tenant.cell_id, tenant.tenant_id), None)


def copy_tenant_db(store: Store, tenant: Tenant, target_cell_id: str) -> dict:
    src = store.tenant_dbs.get(tenant.tenant_id)
    if not src:
        raise ValueError("source database missing")
    copied = copy.deepcopy(src)
    copied["cell_id"] = target_cell_id
    copied["copy_checksum"] = hashlib.sha256(json.dumps(src["rows"], sort_keys=True).encode()).hexdigest()
    return copied


def validate_copy(src: dict, dest: dict) -> bool:
    return src["rows"] == dest["rows"] and src["sequences"] == dest["sequences"]


def cache_key(tenant_id: str, tenant_version: int, suffix: str) -> str:
    return f"t:{tenant_id}:{tenant_version}:{suffix}"


def sign_envelope(payload: dict) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(HMAC_KEY, body, hashlib.sha256).hexdigest()


def verify_envelope(payload: dict, signature: str) -> bool:
    expected = sign_envelope(payload)
    return hmac.compare_digest(expected, signature)


def persist_db_file(data_dir: Path, tenant: Tenant, store: Store) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / f"{tenant.database_name}.json"
    path.write_text(json.dumps(store.tenant_dbs.get(tenant.tenant_id, {}), indent=2))
