import asyncio

from sqlalchemy import select

from tenant_flow.db.session import AsyncSessionLocal
from tenant_flow.models.tenant import Tenant


async def main():
    # NO middleware, NO dependency, NO SET LOCAL
    # Solo abrimos session y hacemos query directa
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Tenant))
        tenants = result.scalars().all()
        print(f"Got {len(tenants)} tenants")


asyncio.run(main())
