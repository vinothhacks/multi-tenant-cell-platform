from __future__ import annotations

from contextvars import ContextVar

tenant_id_var: ContextVar[str | None] = ContextVar("tenant_id", default=None)
tenant_version_var: ContextVar[int | None] = ContextVar("tenant_version", default=None)


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.META.get("HTTP_X_TENANT_ID")
        if not incoming:
            from django.http import JsonResponse

            return JsonResponse({"error": "tenant identity required"}, status=400)
        token = tenant_id_var.set(incoming)
        ver = request.META.get("HTTP_X_TENANT_VERSION")
        vtoken = tenant_version_var.set(int(ver) if ver else 1)
        try:
            from .connections import assert_bound, bind_tenant

            bind_tenant(incoming)
            response = self.get_response(request)
            assert_bound(incoming)
            return response
        finally:
            tenant_id_var.reset(token)
            tenant_version_var.reset(vtoken)
