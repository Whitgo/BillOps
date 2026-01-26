"""Calendar integration models for Google Calendar and Outlook Calendar."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class CalendarIntegration(Base):
    """Calendar integration credentials and sync configuration."""
    __tablename__ = "calendar_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # google | microsoft
    provider_calendar_id = Column(String(255), nullable=False)  # Calendar ID from provider
    calendar_name = Column(String(255), nullable=True)  # Display name
    is_active = Column(Boolean, nullable=False, default=True)
    sync_enabled = Column(Boolean, nullable=False, default=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    sync_interval_minutes = Column(Integer, nullable=False, default=60)  # How often to sync
    
    # OAuth tokens (from UserOAuthAccount, but stored here for convenience)
    oauth_account_id = Column(UUID(as_uuid=True), ForeignKey("user_oauth_accounts.id", ondelete="SET NULL"), nullable=True)
    
    # Sync configuration
    sync_config = Column(JSON, nullable=True, default={})  # Additional sync settings
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    oauth_account = relationship("UserOAuthAccount", foreign_keys=[oauth_account_id])
    synced_events = relationship("SyncedCalendarEvent", back_populates="calendar_integration", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<CalendarIntegration(id={self.id}, provider={self.provider}, user_id={self.user_id})>"


class SyncedCalendarEvent(Base):
    """Tracked calendar events synced from external providers."""
    __tablename__ = "synced_calendar_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    calendar_integration_id = Column(UUID(as_uuid=True), ForeignKey("calendar_integrations.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_event_id = Column(String(255), nullable=False)  # ID from provider
    event_summary = Column(String(500), nullable=True)
    event_description = Column(String(2000), nullable=True)
    event_start = Column(DateTime(timezone=True), nullable=False)
    event_end = Column(DateTime(timezone=True), nullable=False)
    
    # Linked time entry (if converted to billable)
    time_entry_id = Column(UUID(as_uuid=True), ForeignKey("time_entries.id", ondelete="SET NULL"), nullable=True)
    
    # Sync metadata
    is_synced = Column(Boolean, nullable=False, default=False)  # Whether a time entry was created
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    calendar_integration = relationship("CalendarIntegration", back_populates="synced_events")

    def __repr__(self) -> str:
        return f"<SyncedCalendarEvent(id={self.id}, event_summary={self.event_summary})>"


class SlackIntegration(Base):
    """Slack workspace integration for notifications and commands."""
    __tablename__ = "slack_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(String(100), nullable=False, unique=True)  # Slack workspace ID
    workspace_name = Column(String(255), nullable=True)
    bot_token = Column(String(500), nullable=False)  # xoxb- token
    app_id = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Features enabled
    notify_time_entries = Column(Boolean, nullable=False, default=True)
    notify_invoices = Column(Boolean, nullable=False, default=False)
    slash_commands_enabled = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<SlackIntegration(workspace_id={self.workspace_id})>"


class SlackUserBinding(Base):
    """Link between BillOps users and Slack users."""
    __tablename__ = "slack_user_bindings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    slack_integration_id = Column(UUID(as_uuid=True), ForeignKey("slack_integrations.id", ondelete="CASCADE"), nullable=False)
    slack_user_id = Column(String(100), nullable=False)  # U1234567890
    slack_username = Column(String(255), nullable=True)
    slack_email = Column(String(255), nullable=True)
    
    # Notification preferences
    notify_daily_summary = Column(Boolean, nullable=False, default=False)
    notify_invoice_ready = Column(Boolean, nullable=False, default=False)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<SlackUserBinding(user_id={self.user_id}, slack_user_id={self.slack_user_id})>"
