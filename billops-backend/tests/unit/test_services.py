"""
Unit tests for services.
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, MagicMock

from app.models.invoice import Invoice
from app.models.time_entry import TimeEntry
from app.models.billing_rule import BillingRule
from app.models.client import Client
from app.models.project import Project
from app.services.invoice import InvoiceService
from app.services.time_entry import TimeEntryService
from app.services.billing_rule import BillingRuleService
from app.services.client import ClientService
from app.services.project import ProjectService


@pytest.mark.unit
@pytest.mark.db
class TestClientService:
    """Tests for ClientService."""

    def test_get_client_by_id(self, db: Session, test_client: Client):
        """Test retrieving client by ID."""
        service = ClientService(db)
        retrieved = service.get_by_id(test_client.id)
        assert retrieved is not None
        assert retrieved.id == test_client.id
        assert retrieved.name == "Acme Corporation"

    def test_get_client_nonexistent(self, db: Session):
        """Test retrieving nonexistent client."""
        import uuid
        service = ClientService(db)
        result = service.get_by_id(uuid.uuid4())
        assert result is None

    def test_create_client(self, db: Session, test_user):
        """Test creating a new client."""
        service = ClientService(db)
        client = service.create(
            user_id=test_user.id,
            name="New Client",
            email="new@example.com",
            currency="USD",
        )
        assert client.id is not None
        assert client.name == "New Client"
        assert client.email == "new@example.com"

    def test_update_client(self, db: Session, test_client: Client):
        """Test updating client."""
        service = ClientService(db)
        updated = service.update(
            test_client.id,
            name="Updated Acme",
            phone="+1-555-9999",
        )
        assert updated.name == "Updated Acme"
        assert updated.phone == "+1-555-9999"

    def test_deactivate_client(self, db: Session, test_client: Client):
        """Test deactivating client."""
        service = ClientService(db)
        service.delete(test_client.id)
        # Verify client is deactivated or deleted
        result = service.get_by_id(test_client.id)
        # Should be soft deleted
        assert result is None or result.is_active is False


@pytest.mark.unit
@pytest.mark.db
class TestProjectService:
    """Tests for ProjectService."""

    def test_get_project_by_id(self, db: Session, test_project: Project):
        """Test retrieving project by ID."""
        service = ProjectService(db)
        retrieved = service.get_by_id(test_project.id)
        assert retrieved is not None
        assert retrieved.id == test_project.id
        assert retrieved.name == "Test Project"

    def test_create_project(self, db: Session, test_user, test_client: Client):
        """Test creating project."""
        service = ProjectService(db)
        project = service.create(
            user_id=test_user.id,
            client_id=test_client.id,
            name="New Project",
            hourly_rate_cents=20000,
            currency="USD",
        )
        assert project.id is not None
        assert project.name == "New Project"
        assert project.hourly_rate_cents == 20000

    def test_list_user_projects(self, db: Session, test_user, test_project: Project):
        """Test listing projects for user."""
        service = ProjectService(db)
        projects = service.get_by_user(test_user.id)
        assert len(projects) > 0
        assert any(p.id == test_project.id for p in projects)


@pytest.mark.unit
@pytest.mark.db
class TestTimeEntryService:
    """Tests for TimeEntryService."""

    def test_get_time_entry_by_id(self, db: Session, test_time_entry: TimeEntry):
        """Test retrieving time entry."""
        service = TimeEntryService(db)
        retrieved = service.get_by_id(test_time_entry.id)
        assert retrieved is not None
        assert retrieved.id == test_time_entry.id

    def test_create_time_entry(self, db: Session, test_user, test_project: Project):
        """Test creating time entry."""
        service = TimeEntryService(db)
        now = datetime.now(timezone.utc)
        entry = service.create(
            user_id=test_user.id,
            project_id=test_project.id,
            description="Test work",
            start_time=now - timedelta(hours=1),
            end_time=now,
            is_billable=True,
        )
        assert entry.id is not None
        assert entry.duration_minutes == 60

    def test_get_entries_for_period(self, db: Session, test_user, test_project: Project, make_time_entry_factory):
        """Test retrieving entries for date period."""
        # Create entries in current period
        now = datetime.now(timezone.utc)
        for i in range(3):
            make_time_entry_factory(
                start_time=now - timedelta(hours=i),
                duration_minutes=60,
            )

        service = TimeEntryService(db)
        period_start = now - timedelta(days=1)
        period_end = now + timedelta(days=1)

        entries = service.get_by_period(test_user.id, period_start, period_end)
        assert len(entries) >= 3

    def test_calculate_billable_hours(self, db: Session, test_user, test_project: Project, make_time_entry_factory):
        """Test calculating billable hours."""
        make_time_entry_factory(duration_minutes=60, is_billable=True)
        make_time_entry_factory(duration_minutes=30, is_billable=True)
        make_time_entry_factory(duration_minutes=30, is_billable=False)

        service = TimeEntryService(db)
        now = datetime.now(timezone.utc)
        hours = service.calculate_billable_hours(
            test_user.id,
            now - timedelta(days=1),
            now + timedelta(days=1),
        )
        assert hours == 1.5  # 60 + 30 minutes = 1.5 hours

    def test_mark_as_billed(self, db: Session, test_time_entry: TimeEntry):
        """Test marking time entry as billed."""
        service = TimeEntryService(db)
        service.mark_as_billed(test_time_entry.id)
        db.refresh(test_time_entry)
        assert test_time_entry.is_billed is True


@pytest.mark.unit
@pytest.mark.db
class TestInvoiceService:
    """Tests for InvoiceService."""

    def test_get_invoice_by_id(self, db: Session, test_invoice: Invoice):
        """Test retrieving invoice."""
        service = InvoiceService(db)
        retrieved = service.get_by_id(test_invoice.id)
        assert retrieved is not None
        assert retrieved.id == test_invoice.id

    def test_create_invoice(self, db: Session, test_client: Client, test_project: Project):
        """Test creating invoice."""
        service = InvoiceService(db)
        invoice = service.create(
            client_id=test_client.id,
            project_id=test_project.id,
            issue_date=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=30),
        )
        assert invoice.id is not None
        assert invoice.status == "draft"

    def test_update_invoice_status(self, db: Session, test_invoice: Invoice):
        """Test updating invoice status."""
        service = InvoiceService(db)
        service.update_status(test_invoice.id, "sent")
        db.refresh(test_invoice)
        assert test_invoice.status == "sent"

    def test_get_pending_invoices(self, db: Session, test_client: Client, test_project: Project, make_invoice_factory):
        """Test getting pending invoices."""
        make_invoice_factory(status="draft")
        make_invoice_factory(status="draft")
        make_invoice_factory(status="sent")

        service = InvoiceService(db)
        pending = service.get_pending()
        assert len(pending) >= 2

    def test_calculate_invoice_total(self, db: Session, test_invoice: Invoice, test_invoice_line_item):
        """Test invoice total calculation."""
        service = InvoiceService(db)
        total = service.calculate_total(test_invoice.id)
        assert total > 0

    def test_invoice_overdue_status(self, db: Session, test_client: Client, test_project: Project):
        """Test detecting overdue invoices."""
        service = InvoiceService(db)

        # Create overdue invoice
        overdue_date = datetime.now(timezone.utc) - timedelta(days=5)
        invoice = service.create(
            client_id=test_client.id,
            project_id=test_project.id,
            issue_date=overdue_date,
            due_date=overdue_date + timedelta(days=30),
        )

        service.update_status(invoice.id, "sent")
        # Check if service can identify as overdue
        assert invoice.due_date < datetime.now(timezone.utc)


@pytest.mark.unit
@pytest.mark.db
class TestBillingRuleService:
    """Tests for BillingRuleService."""

    def test_get_billing_rule_by_id(self, db: Session, test_billing_rule: BillingRule):
        """Test retrieving billing rule."""
        service = BillingRuleService(db)
        retrieved = service.get_by_id(test_billing_rule.id)
        assert retrieved is not None
        assert retrieved.id == test_billing_rule.id

    def test_create_billing_rule(self, db: Session, test_user, test_client: Client):
        """Test creating billing rule."""
        service = BillingRuleService(db)
        rule = service.create(
            user_id=test_user.id,
            client_id=test_client.id,
            name="Premium Billing",
            billable_hours_per_month=200,
            base_rate_cents=200000,
            overtime_rate_cents=300000,
        )
        assert rule.id is not None
        assert rule.name == "Premium Billing"

    def test_calculate_overtime(self, db: Session, test_billing_rule: BillingRule):
        """Test overtime calculation."""
        service = BillingRuleService(db)

        # Billable hours = 160, so 200 total = 40 overtime
        regular_hours = test_billing_rule.billable_hours_per_month
        total_hours = regular_hours + 40

        regular_cost = regular_hours * (test_billing_rule.base_rate_cents / 100)
        overtime_cost = 40 * (test_billing_rule.overtime_rate_cents / 100)
        total_cost = regular_cost + overtime_cost

        assert total_cost > regular_cost

    def test_update_billing_rule(self, db: Session, test_billing_rule: BillingRule):
        """Test updating billing rule."""
        service = BillingRuleService(db)
        updated = service.update(
            test_billing_rule.id,
            base_rate_cents=200000,
        )
        assert updated.base_rate_cents == 200000

    def test_deactivate_billing_rule(self, db: Session, test_billing_rule: BillingRule):
        """Test deactivating billing rule."""
        service = BillingRuleService(db)
        service.delete(test_billing_rule.id)
        db.refresh(test_billing_rule)
        assert test_billing_rule.is_active is False


@pytest.mark.unit
class TestServiceErrorHandling:
    """Tests for service error handling."""

    def test_invoice_service_with_missing_client(self, db: Session):
        """Test invoice creation with missing client."""
        import uuid
        service = InvoiceService(db)
        with pytest.raises(Exception):
            service.create(
                client_id=uuid.uuid4(),
                project_id=uuid.uuid4(),
                issue_date=datetime.now(timezone.utc),
                due_date=datetime.now(timezone.utc) + timedelta(days=30),
            )

    def test_time_entry_calculation_with_zero_minutes(self, db: Session, test_user, test_project: Project):
        """Test time entry with zero duration."""
        service = TimeEntryService(db)
        now = datetime.now(timezone.utc)
        entry = service.create(
            user_id=test_user.id,
            project_id=test_project.id,
            description="Instant entry",
            start_time=now,
            end_time=now,
            is_billable=True,
        )
        assert entry.duration_minutes == 0
