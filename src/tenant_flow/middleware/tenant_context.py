import secrets
from uuid import UUID

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from tenant_flow.config import settings


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def _handle_admin(self, request: Request, call_next):
        admin_token = request.headers.get("X-Admin-Token")
        if not admin_token:
            return JSONResponse(status_code=401, content={"error": "Missing X-Admin-Token header"})
        if not secrets.compare_digest(admin_token, settings.admin_token):
            return JSONResponse(status_code=401, content={"error": "Invalid X-Admin-Token"})
        return await call_next(request)

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/":
            return await call_next(request)

        if request.url.path.startswith("/admin/"):
            return await self._handle_admin(request, call_next)

        tenant_id_header = request.headers.get("X-Tenant-ID")

        if not tenant_id_header:
            return JSONResponse(
                status_code=401,
                content={"error": "Missing X-Tenant-ID header"},
            )

        try:
            tenant_id = UUID(tenant_id_header)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid X-Tenant-ID format (must be UUID)"},
            )

        request.state.tenant_id = tenant_id
        return await call_next(request)
