"""Add calendar and slack integrations models

Revision ID: 4a8c9b1d2e3f
Revises: 3e76ab6fe679
Create Date: 2026-01-24 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a8c9b1d2e3f'
down_revision: Union[str, Sequence[str], None] = '3e76ab6fe679'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create calendar_integrations table
    op.create_table(
        'calendar_integrations',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('oauth_account_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('provider_calendar_id', sa.String(255), nullable=False),
        sa.Column('calendar_name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sync_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['oauth_account_id'], ['user_oauth_accounts.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_calendar_integrations_user_id', 'calendar_integrations', ['user_id'])
    op.create_index('ix_calendar_integrations_provider', 'calendar_integrations', ['provider'])
    
    # Create synced_calendar_events table
    op.create_table(
        'synced_calendar_events',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('calendar_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('time_entry_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('provider_event_id', sa.String(255), nullable=False),
        sa.Column('event_title', sa.String(255), nullable=False),
        sa.Column('event_description', sa.Text(), nullable=True),
        sa.Column('event_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_synced', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['calendar_id'], ['calendar_integrations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['time_entry_id'], ['time_entries.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_synced_calendar_events_calendar_id', 'synced_calendar_events', ['calendar_id'])
    op.create_index('ix_synced_calendar_events_provider_event_id', 'synced_calendar_events', ['provider_event_id'])
    
    # Create slack_integrations table
    op.create_table(
        'slack_integrations',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', sa.String(255), nullable=False),
        sa.Column('workspace_name', sa.String(255), nullable=False),
        sa.Column('bot_token', sa.Text(), nullable=False),
        sa.Column('app_id', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notifications_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('time_capture_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id'),
    )
    op.create_index('ix_slack_integrations_workspace_id', 'slack_integrations', ['workspace_id'])
    
    # Create slack_user_bindings table
    op.create_table(
        'slack_user_bindings',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('slack_integration_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('slack_user_id', sa.String(255), nullable=False),
        sa.Column('slack_username', sa.String(255), nullable=False),
        sa.Column('slack_email', sa.String(255), nullable=True),
        sa.Column('notify_time_entry_created', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notify_invoice_ready', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notify_daily_summary', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['slack_integration_id'], ['slack_integrations.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_slack_user_bindings_user_id', 'slack_user_bindings', ['user_id'])
    op.create_index('ix_slack_user_bindings_slack_user_id', 'slack_user_bindings', ['slack_user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop slack_user_bindings table
    op.drop_index('ix_slack_user_bindings_slack_user_id', 'slack_user_bindings')
    op.drop_index('ix_slack_user_bindings_user_id', 'slack_user_bindings')
    op.drop_table('slack_user_bindings')
    
    # Drop slack_integrations table
    op.drop_index('ix_slack_integrations_workspace_id', 'slack_integrations')
    op.drop_table('slack_integrations')
    
    # Drop synced_calendar_events table
    op.drop_index('ix_synced_calendar_events_provider_event_id', 'synced_calendar_events')
    op.drop_index('ix_synced_calendar_events_calendar_id', 'synced_calendar_events')
    op.drop_table('synced_calendar_events')
    
    # Drop calendar_integrations table
    op.drop_index('ix_calendar_integrations_provider', 'calendar_integrations')
    op.drop_index('ix_calendar_integrations_user_id', 'calendar_integrations')
    op.drop_table('calendar_integrations')
