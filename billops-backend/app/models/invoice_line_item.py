import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    time_entry_id = Column(UUID(as_uuid=True), ForeignKey("time_entries.id", ondelete="SET NULL"), nullable=True)
    description = Column(String(255), nullable=False)
    quantity = Column(String(50), nullable=False)
    unit_price_cents = Column(Integer, nullable=False)
    amount_cents = Column(Integer, nullable=False)
    billing_rule_snapshot = Column(JSON, nullable=False, default={})

    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")

    def __repr__(self) -> str:
        return f"<InvoiceLineItem(id={self.id}, invoice_id={self.invoice_id}, amount_cents={self.amount_cents})>"
