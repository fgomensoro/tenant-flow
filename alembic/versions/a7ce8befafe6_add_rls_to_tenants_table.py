"""add RLS to tenants table

Revision ID: a7ce8befafe6
Revises: a97bc88abcff
Create Date: 2026-05-04 20:26:36.234600

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7ce8befafe6"
down_revision: str | Sequence[str] | None = "a97bc88abcff"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE tenants FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation ON tenants
        USING (id = current_setting('app.current_tenant')::UUID)
        WITH CHECK (id = current_setting('app.current_tenant')::UUID);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON tenants;")
    op.execute("ALTER TABLE tenants NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE tenants DISABLE ROW LEVEL SECURITY;")
