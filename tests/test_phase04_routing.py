import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-plane"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cellapp.settings")

import django  # noqa: E402

django.setup()

from django.test import Client  # noqa: E402
from cellapp.celery_envelope import TenantTask, sign_envelope  # noqa: E402
from cellapp.connections import alias_for  # noqa: E402


@pytest.fixture
def django_client(tmp_path, monkeypatch):
    from django.conf import settings

    settings.DATA_DIR = tmp_path
    return Client()


def test_i1_missing_tenant(django_client):
    r = django_client.get("/ready")
    assert r.status_code == 400


def test_i2_tenant_a_cannot_read_b(django_client):
    a = django_client.get("/ready", HTTP_X_TENANT_ID="aaa")
    b = django_client.get("/ready", HTTP_X_TENANT_ID="bbb")
    assert a.status_code == 200
    assert b.status_code == 200
    assert a.json()["alias"] != b.json()["alias"]
    assert Path(a.json()["database"]) != Path(b.json()["database"])
    probe = django_client.get("/isolation-probe?other=bbb", HTTP_X_TENANT_ID="aaa")
    assert probe.status_code == 403
    assert probe.json()["result"] == "BLOCKED"


def test_default_alias_not_used_for_tenant_data(django_client):
    r = django_client.get("/ready", HTTP_X_TENANT_ID="ccc")
    assert r.json()["default_unused_for_tenant_data"] is True
    assert alias_for("ccc") != "default"


def test_signed_celery_envelope():
    sig = sign_envelope("t1", 1, {"job": "x"})
    assert TenantTask().apply("t1", 1, {"job": "x"}, sig)["ok"] is True
    with pytest.raises(PermissionError):
        TenantTask().apply("t1", 1, {"job": "x"}, None)
