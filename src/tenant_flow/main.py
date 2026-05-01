from fastapi import FastAPI

from tenant_flow.middleware.tenant_context import TenantContextMiddleware

app = FastAPI(title="tenant-flow")
app.add_middleware(TenantContextMiddleware)


@app.get("/")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "tenant-flow"}
