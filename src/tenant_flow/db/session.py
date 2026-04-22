from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tenant_flow.db.engine import engine

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
)
