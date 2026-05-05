from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tenant_flow.dependencies.tenant_session import get_tenant_session
from tenant_flow.models.tenant import Tenant

router = APIRouter()

TenantSession = Annotated[AsyncSession, Depends(get_tenant_session)]


@router.get("/tenants")
async def list_tenants(session: TenantSession):
    result = await session.execute(select(Tenant))
    tenants = result.scalars().all()
    return [{"id": str(t.id), "name": t.name, "slug": t.slug} for t in tenants]
