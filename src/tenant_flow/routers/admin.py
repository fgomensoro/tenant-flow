from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text
from uuid_utils import uuid7

from tenant_flow.db.session import AsyncSessionLocal
from tenant_flow.models.tenant import Tenant
from tenant_flow.schemas.tenant import TenantCreate, TenantResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/tenants", response_model=TenantResponse, status_code=201)
async def create_tenant(payload: TenantCreate, request: Request) -> Tenant:
    new_id = UUID(str(uuid7()))

    async with AsyncSessionLocal() as session:
        # Set tenant context (same pattern as seed) so RLS WITH CHECK passes
        await session.execute(
            text("SELECT set_config('app.current_tenant', :tid, true)"),
            {"tid": str(new_id)},
        )

        tenant = Tenant(id=new_id, name=payload.name, slug=payload.slug)
        session.add(tenant)

        try:
            await session.flush()
            await session.refresh(tenant)
            await session.commit()
        except Exception as e:
            await session.rollback()
            if "unique" in str(e).lower():
                raise HTTPException(
                    status_code=409,
                    detail=f"Tenant with slug '{payload.slug}' already exists",
                ) from e
            raise

        return tenant