import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class BillingRule(Base):
    __tablename__ = "billing_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_type = Column(String(50), nullable=False)  # hourly | fixed | retainer
    rate_cents = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    rounding_increment_minutes = Column(Integer, nullable=True, default=0)
    overtime_multiplier = Column(Numeric(6, 2), nullable=True, default=1.0)
    cap_hours = Column(Numeric(12, 2), nullable=True)
    retainer_hours = Column(Numeric(12, 2), nullable=True)
    effective_from = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    effective_to = Column(DateTime(timezone=True), nullable=True)
    meta = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    project = relationship("Project", back_populates="billing_rules")
    time_entries = relationship("TimeEntry", back_populates="billing_rule")
