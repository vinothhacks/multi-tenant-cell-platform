from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from django.conf import settings
from django.db import connections

from .middleware import tenant_id_var

MAX_ALIASES = 64
_LRU: OrderedDict[str, str] = OrderedDict()


def alias_for(tenant_id: str) -> str:
    return "t_" + tenant_id.replace("-", "_")


def db_path(tenant_id: str) -> Path:
    return Path(settings.DATA_DIR) / f"db_{tenant_id.replace('-', '_')}.sqlite3"


def bind_tenant(tenant_id: str) -> str:
    """Register a per-tenant SQLite alias. Never use default for tenant data."""
    alias = alias_for(tenant_id)
    path = db_path(tenant_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    connections.databases[alias] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(path),
        "ATOMIC_REQUESTS": False,
        "AUTOCOMMIT": True,
        "CONN_MAX_AGE": 0,
        "OPTIONS": {},
        "TIME_ZONE": None,
        "CONN_HEALTH_CHECKS": False,
        "HOST": "",
        "PORT": "",
        "USER": "",
        "PASSWORD": "",
    }
    _LRU[alias] = tenant_id
    _LRU.move_to_end(alias)
    while len(_LRU) > MAX_ALIASES:
        old, _ = _LRU.popitem(last=False)
        connections.databases.pop(old, None)
        try:
            connections[old].close()
        except Exception:
            pass
    return alias


def assert_bound(tenant_id: str) -> None:
    alias = alias_for(tenant_id)
    conn = connections[alias]
    name = conn.settings_dict.get("NAME", "")
    expected = str(db_path(tenant_id))
    if Path(name) != Path(expected):
        raise RuntimeError("current_database != expected_database")
    if tenant_id_var.get() != tenant_id:
        raise RuntimeError("tenant context mismatch")


def evict(tenant_id: str) -> None:
    alias = alias_for(tenant_id)
    _LRU.pop(alias, None)
    connections.databases.pop(alias, None)
    try:
        connections[alias].close()
    except Exception:
        pass


class TenantRouter:
    def db_for_read(self, model, **hints):
        tid = tenant_id_var.get()
        if not tid:
            return None
        return alias_for(tid)

    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)

    def allow_migrate(self, db, app_label, **hints):
        if db == "default":
            return app_label != "cellapp"
        return True
