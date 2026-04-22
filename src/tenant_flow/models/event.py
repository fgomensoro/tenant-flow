from datetime import datetime
from uuid import UUID

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Text, text, ForeignKey, LargeBinary, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from tenant_flow.models.base import Base

class Event(Base):
  __tablename__ = "events"
  
  id: Mapped[UUID] = mapped_column(primary_key=True)
  tenant_id: Mapped[UUID] = mapped_column( ForeignKey("tenants.id"), nullable=False)
  provider: Mapped[str] = mapped_column(Text, nullable=False)
  event_type: Mapped[str] = mapped_column(Text, nullable=False)
  idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
  body_hash: Mapped[str] = mapped_column(Text, nullable=False)
  raw_body: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
  payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
  received_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
  current_status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'received'"))
  last_attempted_at: Mapped[datetime | None] = mapped_column()
  attempt_count: Mapped[int] = mapped_column(nullable=False, server_default=text("0"))
  
  __table_args__ = (
        UniqueConstraint("tenant_id", "provider", "idempotency_key"),
    )