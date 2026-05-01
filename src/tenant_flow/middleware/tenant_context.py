from uuid import UUID

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip tenant check for health endpoint
        if request.url.path == "/":
            return await call_next(request)

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
