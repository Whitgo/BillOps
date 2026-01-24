from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field


class InvoiceCreate(BaseModel):
    """Schema for creating a new invoice."""
    client_id: UUID
    project_id: UUID | None = None
    invoice_number: str = Field(..., min_length=1, max_length=50)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    issue_date: date | None = None
    due_date: date | None = None
    notes: str | None = None
    meta: dict | None = None


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""
    status: str | None = None  # draft | sent | paid | partial | overdue | canceled
    due_date: date | None = None
    notes: str | None = None
    meta: dict | None = None


class InvoiceResponse(BaseModel):
    """Schema for invoice response."""
    id: UUID
    client_id: UUID
    project_id: UUID | None
    invoice_number: str
    currency: str
    status: str
    issue_date: datetime
    due_date: datetime | None
    subtotal_cents: int
    tax_cents: int
    total_cents: int
    notes: str | None
    meta: dict | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceDetailResponse(InvoiceResponse):
    """Schema for detailed invoice response with line items."""
    line_item_count: int | None = None
    payment_count: int | None = None
    amount_paid_cents: int | None = None
