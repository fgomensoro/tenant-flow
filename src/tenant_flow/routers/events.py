from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tenant_flow.dependencies.tenant_session import get_tenant_session
from tenant_flow.models.event import Event
from tenant_flow.schemas.event import EventResponse

router = APIRouter()

TenantSession = Annotated[AsyncSession, Depends(get_tenant_session)]


@router.get("/events")
async def get_events(session: TenantSession, limit: int = Query(default=20, le=100, ge=1),
    after: UUID | None = Query(default=None),) -> list[EventResponse]:
    stmt = select(Event).order_by(Event.id).limit(limit)
    if after:
        stmt = stmt.where(Event.id > after)
        
    result = await session.execute(stmt)
    events = result.scalars().all()
    
    return events
  
  
@router.get("/events/{event_id}")
async def get_event(event_id: UUID,session: TenantSession) -> EventResponse:
    
    result = await session.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event