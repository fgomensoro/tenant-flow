from fastapi import FastAPI

from tenant_flow.middleware.tenant_context import TenantContextMiddleware
from tenant_flow.routers import admin, tenants, events

app = FastAPI(title="tenant-flow")
app.add_middleware(TenantContextMiddleware)
app.include_router(admin.router)
app.include_router(events.router)
app.include_router(tenants.router)


@app.get("/")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "tenant-flow"}
