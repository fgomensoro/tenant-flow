from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tenant_flow.dependencies.tenant_session import get_tenant_session
from tenant_flow.models.tenant import Tenant
from tenant_flow.schemas.tenant import TenantResponse

router = APIRouter()

TenantSession = Annotated[AsyncSession, Depends(get_tenant_session)]


@router.get("/tenants/me")
async def get_current_tenant(session: TenantSession, request: Request) -> TenantResponse:
    tenant_id = request.state.tenant_id
    result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return tenant
