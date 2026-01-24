from datetime import datetime
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field


class BillingRuleCreate(BaseModel):
    """Schema for creating a new billing rule."""
    project_id: UUID
    rule_type: str = Field(..., min_length=1)  # hourly | fixed | retainer
    rate_cents: int = Field(..., ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    rounding_increment_minutes: int | None = None
    overtime_multiplier: Decimal | None = None
    cap_hours: Decimal | None = None
    retainer_hours: Decimal | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    meta: dict | None = None


class BillingRuleUpdate(BaseModel):
    """Schema for updating a billing rule."""
    rule_type: str | None = None
    rate_cents: int | None = None
    currency: str | None = None
    rounding_increment_minutes: int | None = None
    overtime_multiplier: Decimal | None = None
    cap_hours: Decimal | None = None
    retainer_hours: Decimal | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    meta: dict | None = None


class BillingRuleResponse(BaseModel):
    """Schema for billing rule response."""
    id: UUID
    project_id: UUID
    rule_type: str
    rate_cents: int
    currency: str
    rounding_increment_minutes: int | None
    overtime_multiplier: Decimal | None
    cap_hours: Decimal | None
    retainer_hours: Decimal | None
    effective_from: datetime
    effective_to: datetime | None
    meta: dict | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
