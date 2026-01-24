"""Initial schema: users, clients, projects, time entries, billing rules, invoices, payments

Revision ID: 3e76ab6fe679
Revises: 
Create Date: 2026-01-24 21:08:33.905300

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e76ab6fe679'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='member'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # Create user_oauth_accounts table
    op.create_table(
        'user_oauth_accounts',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('provider_account_id', sa.String(255), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'provider_account_id', name='uq_provider_account'),
    )

    # Create clients table
    op.create_table(
        'clients',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('contact_name', sa.String(255), nullable=True),
        sa.Column('created_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('default_billing_rule_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_projects_client_id', 'projects', ['client_id'])

    # Create billing_rules table
    op.create_table(
        'billing_rules',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('rate_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('rounding_increment_minutes', sa.Integer(), nullable=True),
        sa.Column('overtime_multiplier', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('cap_hours', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('retainer_hours', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_billing_rules_project_id', 'billing_rules', ['project_id'])

    # Fix foreign key constraint in projects for billing_rules
    op.create_foreign_key('fk_projects_default_billing_rule_id', 'projects', 'billing_rules',
                         ['default_billing_rule_id'], ['id'], ondelete='SET NULL')

    # Create time_entries table
    op.create_table(
        'time_entries',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('billing_rule_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('context_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['billing_rule_id'], ['billing_rules.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_time_entries_project_id', 'time_entries', ['project_id'])
    op.create_index('ix_time_entries_user_id', 'time_entries', ['user_id'])
    op.create_index('ix_time_entries_status', 'time_entries', ['status'])

    # Create invoices table
    op.create_table(
        'invoices',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('invoice_number', sa.String(50), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('issue_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('subtotal_cents', sa.Integer(), nullable=False),
        sa.Column('tax_cents', sa.Integer(), nullable=False),
        sa.Column('total_cents', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_number'),
    )
    op.create_index('ix_invoices_client_id', 'invoices', ['client_id'])

    # Create invoice_line_items table
    op.create_table(
        'invoice_line_items',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('invoice_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('time_entry_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('description', sa.String(255), nullable=False),
        sa.Column('quantity', sa.String(50), nullable=False),
        sa.Column('unit_price_cents', sa.Integer(), nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('billing_rule_snapshot', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['time_entry_id'], ['time_entries.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_invoice_line_items_invoice_id', 'invoice_line_items', ['invoice_id'])

    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('invoice_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('method', sa.String(50), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reference', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_payments_invoice_id', 'payments', ['invoice_id'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_email', sa.String(255), nullable=True),
        sa.Column('action', sa.String(255), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('audit_logs')
    op.drop_table('payments')
    op.drop_table('invoice_line_items')
    op.drop_table('invoices')
    op.drop_table('time_entries')
    op.drop_constraint('fk_projects_default_billing_rule_id', 'projects', type_='foreignkey')
    op.drop_table('billing_rules')
    op.drop_table('projects')
    op.drop_table('clients')
    op.drop_table('user_oauth_accounts')
    op.drop_table('users')
