from datetime import datetime
from uuid import UUID

from sqlalchemy import Text, text
from sqlalchemy.orm import Mapped, mapped_column

from tenant_flow.models.base import Base

class Tenant(Base):
  __tablename__ = "tenants"
  
  id: Mapped[UUID] = mapped_column(primary_key=True)
  name: Mapped[str] = mapped_column(Text, nullable=False)
  slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
  created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
  updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    