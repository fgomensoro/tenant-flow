from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from tenant_flow.config import settings

engine: AsyncEngine = create_async_engine(settings.database_url, echo=settings.debug)
