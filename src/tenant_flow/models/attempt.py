from datetime import datetime
from uuid import UUID

from sqlalchemy import Text, text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from tenant_flow.models.base import Base


class EventProcessingAttempt(Base):
    __tablename__ = "event_processing_attempts"
    
    id: Mapped[UUID] = mapped_column(primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id"), nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    status: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int | None] = mapped_column()