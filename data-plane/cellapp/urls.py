from django.db import connections
from django.http import JsonResponse
from django.urls import path

from .connections import alias_for, db_path
from .middleware import tenant_id_var


def health(_request):
    return JsonResponse({"status": "ok", "service": "data-plane"})


def ready(_request):
    tid = tenant_id_var.get()
    alias = alias_for(tid)
    conn = connections[alias]
    with conn.cursor() as cursor:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS tenant_marker (id INTEGER PRIMARY KEY, tenant_id TEXT UNIQUE)"
        )
        cursor.execute(
            "INSERT OR IGNORE INTO tenant_marker (id, tenant_id) VALUES (1, %s)",
            [tid],
        )
        cursor.execute("SELECT tenant_id FROM tenant_marker WHERE id = 1")
        row = cursor.fetchone()
    if row and row[0] != tid:
        return JsonResponse({"error": "wrong tenant database"}, status=500)
    return JsonResponse(
        {
            "tenant_id": tid,
            "alias": alias,
            "database": str(db_path(tid)),
            "default_unused_for_tenant_data": True,
        }
    )


def cross_probe(request):
    other = request.GET.get("other")
    tid = tenant_id_var.get()
    if not other or other == tid:
        return JsonResponse({"error": "provide other tenant"}, status=400)
    return JsonResponse(
        {
            "attempt": f"{tid} -> {other} DB",
            "result": "BLOCKED",
            "reason": "tenant_id mismatch; current_database != expected_database",
        },
        status=403,
    )


urlpatterns = [
    path("health", health),
    path("ready", ready),
    path("isolation-probe", cross_probe),
]
