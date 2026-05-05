from collections.abc import AsyncGenerator

from fastapi import HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tenant_flow.db.session import AsyncSessionLocal


async def get_tenant_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    # 1. Recuperar lo que el middleware dejó
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(
            status_code=500,
            detail="Tenant context missing — middleware did not run",
        )

    # 2. Abrir session
    async with AsyncSessionLocal() as session:
        # 3. SET LOCAL con bind parameter
        await session.execute(
            text("SELECT set_config('app.current_tenant', :tid, true)"),
            {"tid": str(tenant_id)},
        )
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
