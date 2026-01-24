from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    """Schema for creating a new client."""
    name: str = Field(..., min_length=1, max_length=255)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    contact_email: str | None = None
    contact_name: str | None = None


class ClientUpdate(BaseModel):
    """Schema for updating a client."""
    name: str | None = None
    currency: str | None = None
    contact_email: str | None = None
    contact_name: str | None = None


class ClientResponse(BaseModel):
    """Schema for client response."""
    id: UUID
    name: str
    currency: str
    contact_email: str | None
    contact_name: str | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClientDetailResponse(ClientResponse):
    """Schema for detailed client response with projects."""
    project_count: int | None = None
