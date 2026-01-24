from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    """Schema for creating a new payment."""
    invoice_id: UUID
    amount_cents: int = Field(..., ge=0)
    method: str | None = None  # ach | card | wire | check | other
    reference: str | None = None


class PaymentUpdate(BaseModel):
    """Schema for updating a payment."""
    method: str | None = None
    reference: str | None = None


class PaymentResponse(BaseModel):
    """Schema for payment response."""
    id: UUID
    invoice_id: UUID
    amount_cents: int
    method: str | None
    received_at: datetime
    reference: str | None
    created_at: datetime

    class Config:
        from_attributes = True
