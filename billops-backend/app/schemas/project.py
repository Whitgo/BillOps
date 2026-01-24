from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""
    client_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    status: str = Field(default="active")
    default_billing_rule_id: UUID | None = None


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: str | None = None
    status: str | None = None
    default_billing_rule_id: UUID | None = None


class ProjectResponse(BaseModel):
    """Schema for project response."""
    id: UUID
    client_id: UUID
    name: str
    status: str
    default_billing_rule_id: UUID | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    """Schema for detailed project response with billing rules."""
    billing_rule_count: int | None = None
    time_entry_count: int | None = None
