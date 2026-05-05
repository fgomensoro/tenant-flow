from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict


class CurrentStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider: str
    event_type: str
    idempotency_key: str
    payload: dict[str, Any]
    received_at: AwareDatetime
    current_status: CurrentStatus
    last_attempted_at: AwareDatetime | None
    attempt_count: int
