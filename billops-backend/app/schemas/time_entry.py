from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class TimeEntryCreate(BaseModel):
    """Schema for creating a new time entry."""
    project_id: UUID
    client_id: UUID
    billing_rule_id: UUID | None = None
    source: str = Field(default="manual")  # auto | manual | imported
    started_at: datetime
    ended_at: datetime
    description: str | None = None
    context_data: dict | None = None


class TimeEntryUpdate(BaseModel):
    """Schema for updating a time entry."""
    project_id: UUID | None = None
    client_id: UUID | None = None
    billing_rule_id: UUID | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    description: str | None = None
    status: str | None = None
    context_data: dict | None = None


class TimeEntryResponse(BaseModel):
    """Schema for time entry response."""
    id: UUID
    user_id: UUID
    project_id: UUID
    client_id: UUID
    billing_rule_id: UUID | None
    source: str
    started_at: datetime
    ended_at: datetime
    duration_minutes: int
    description: str | None
    status: str
    context_data: dict | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
