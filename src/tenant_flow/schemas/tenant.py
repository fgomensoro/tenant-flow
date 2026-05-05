from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict


class TenantCreate(BaseModel):
    name: str
    slug: str


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    created_at: AwareDatetime
    updated_at: AwareDatetime
