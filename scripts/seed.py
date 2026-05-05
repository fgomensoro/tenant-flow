import asyncio
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import OperationalError, ProgrammingError

from tenant_flow.db.session import AsyncSessionLocal
from tenant_flow.models.tenant import Tenant

ACME_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
BETA_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

DEMO_TENANTS = [
    {"id": ACME_ID, "name": "Acme Corp", "slug": "acme"},
    {"id": BETA_ID, "name": "Beta Inc", "slug": "beta"},
]


async def seed():
    try:
        for tenant_data in DEMO_TENANTS:
            async with AsyncSessionLocal() as session:
                await session.execute(
                    text("SELECT set_config('app.current_tenant', :tid, true)"),
                    {"tid": str(tenant_data["id"])},
                )
                await session.execute(
                    pg_insert(Tenant.__table__)
                    .values(**tenant_data)
                    .on_conflict_do_nothing(index_elements=["id"])
                )
                await session.commit()
                print(f"Seeded {tenant_data['slug']}")
    except OperationalError as e:
        print(f"\nERROR: Could not connect to database.\n{e}\n")
        print("Possible causes:")
        print("  1. Postgres is not running. Try: docker compose up -d")
        print("  2. Connection settings wrong in .env")
    except ProgrammingError as e:
        print(f"\nERROR: Database schema issue.\n{e}\n")
        print("Possible causes:")
        print("  1. Migrations have not been applied. Try: uv run alembic upgrade head")
        print("  2. Tenants table is missing or has unexpected schema")
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}\n")
        print("Check that Postgres is running, migrations are applied, and .env is correct.")


if __name__ == "__main__":
    asyncio.run(seed())
