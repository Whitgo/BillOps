"""
Unit tests for models.
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.client import Client
from app.models.project import Project
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.models.billing_rule import BillingRule


@pytest.mark.unit
@pytest.mark.db
class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self, test_user: User):
        """Test user creation with required fields."""
        assert test_user.id is not None
        assert test_user.email == "test@example.com"
        assert test_user.first_name == "Test"
        assert test_user.last_name == "User"
        assert test_user.is_active is True
        assert test_user.is_verified is True

    def test_user_created_at_timestamp(self, test_user: User):
        """Test that user has created_at timestamp."""
        assert test_user.created_at is not None
        assert isinstance(test_user.created_at, datetime)

    def test_user_relationships(self, db: Session, test_user: User, test_client: Client):
        """Test user relationships."""
        assert len(test_user.clients) > 0
        assert test_user.clients[0].name == "Acme Corporation"


@pytest.mark.unit
@pytest.mark.db
class TestClientModel:
    """Tests for Client model."""

    def test_client_creation(self, test_client: Client):
        """Test client creation with required fields."""
        assert test_client.id is not None
        assert test_client.name == "Acme Corporation"
        assert test_client.email == "billing@acme.com"
        assert test_client.currency == "USD"
        assert test_client.is_active is True

    def test_client_phone_optional(self, db: Session, test_user: User):
        """Test that phone is optional."""
        client = Client(
            user_id=test_user.id,
            name="No Phone Client",
            email="nophone@example.com",
            currency="USD",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(client)
        db.commit()
        assert client.phone is None


@pytest.mark.unit
@pytest.mark.db
class TestProjectModel:
    """Tests for Project model."""

    def test_project_creation(self, test_project: Project):
        """Test project creation with required fields."""
        assert test_project.id is not None
        assert test_project.name == "Test Project"
        assert test_project.hourly_rate_cents == 15000
        assert test_project.currency == "USD"
        assert test_project.is_active is True

    def test_project_description_optional(self, db: Session, test_user: User, test_client: Client):
        """Test that description is optional."""
        project = Project(
            user_id=test_user.id,
            client_id=test_client.id,
            name="Simple Project",
            hourly_rate_cents=10000,
            currency="USD",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(project)
        db.commit()
        assert project.description is None or project.description == ""

    def test_project_relationships(self, db: Session, test_project: Project, test_time_entry: TimeEntry):
        """Test project relationships."""
        assert len(test_project.time_entries) > 0
        assert test_project.time_entries[0].description == "Test work session"


@pytest.mark.unit
@pytest.mark.db
class TestTimeEntryModel:
    """Tests for TimeEntry model."""

    def test_time_entry_creation(self, test_time_entry: TimeEntry):
        """Test time entry creation with required fields."""
        assert test_time_entry.id is not None
        assert test_time_entry.description == "Test work session"
        assert test_time_entry.duration_minutes == 60
        assert test_time_entry.is_billable is True
        assert test_time_entry.is_billed is False

    def test_time_entry_duration_calculation(self, db: Session, test_user: User, test_project: Project):
        """Test that duration is calculated correctly."""
        start = datetime.now(timezone.utc)
        end = start + timedelta(hours=2, minutes=30)

        entry = TimeEntry(
            user_id=test_user.id,
            project_id=test_project.id,
            description="Long session",
            start_time=start,
            end_time=end,
            duration_minutes=150,
            is_billable=True,
            is_billed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(entry)
        db.commit()

        assert entry.duration_minutes == 150

    def test_time_entry_non_billable(self, db: Session, test_user: User, test_project: Project):
        """Test creating non-billable time entry."""
        entry = TimeEntry(
            user_id=test_user.id,
            project_id=test_project.id,
            description="Break",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(minutes=30),
            duration_minutes=30,
            is_billable=False,
            is_billed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(entry)
        db.commit()

        assert entry.is_billable is False


@pytest.mark.unit
@pytest.mark.db
class TestInvoiceModel:
    """Tests for Invoice model."""

    def test_invoice_creation(self, test_invoice: Invoice):
        """Test invoice creation with required fields."""
        assert test_invoice.id is not None
        assert test_invoice.invoice_number.startswith("INV-")
        assert test_invoice.status == "draft"
        assert test_invoice.total_cents == 150000
        assert test_invoice.currency == "USD"

    def test_invoice_status_lifecycle(self, db: Session, test_invoice: Invoice):
        """Test invoice status transitions."""
        statuses = ["draft", "sent", "paid", "overdue", "canceled"]

        for status in statuses:
            test_invoice.status = status
            db.commit()
            assert test_invoice.status == status

    def test_invoice_due_date(self, db: Session, test_invoice: Invoice):
        """Test invoice due date is set."""
        assert test_invoice.due_date is not None
        assert test_invoice.due_date > test_invoice.issue_date

    def test_invoice_amount_calculations(self, db: Session, test_invoice: Invoice):
        """Test invoice amount fields."""
        assert test_invoice.subtotal_cents > 0
        assert test_invoice.total_cents == test_invoice.subtotal_cents + test_invoice.tax_cents

    def test_invoice_with_tax(self, db: Session, test_client: Client, test_project: Project):
        """Test invoice with tax calculation."""
        invoice = Invoice(
            client_id=test_client.id,
            project_id=test_project.id,
            invoice_number="INV-TAX-001",
            currency="USD",
            status="draft",
            issue_date=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=30),
            subtotal_cents=100000,  # $1000
            tax_cents=10000,  # $100
            total_cents=110000,  # $1100
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(invoice)
        db.commit()

        assert invoice.subtotal_cents == 100000
        assert invoice.tax_cents == 10000
        assert invoice.total_cents == 110000

    def test_invoice_relationships(self, db: Session, test_invoice: Invoice, test_invoice_line_item):
        """Test invoice relationships."""
        assert len(test_invoice.line_items) > 0
        assert test_invoice.line_items[0].description == "Professional services - 10 hours @ $150/hr"


@pytest.mark.unit
@pytest.mark.db
class TestBillingRuleModel:
    """Tests for BillingRule model."""

    def test_billing_rule_creation(self, test_billing_rule: BillingRule):
        """Test billing rule creation with required fields."""
        assert test_billing_rule.id is not None
        assert test_billing_rule.name == "Standard Billing"
        assert test_billing_rule.base_rate_cents == 150000
        assert test_billing_rule.is_active is True

    def test_billing_rule_overtime_rate(self, test_billing_rule: BillingRule):
        """Test overtime rate configuration."""
        assert test_billing_rule.overtime_rate_cents > test_billing_rule.base_rate_cents

    def test_billing_rule_billable_hours(self, test_billing_rule: BillingRule):
        """Test billable hours per month."""
        assert test_billing_rule.billable_hours_per_month == 160

    def test_billing_rule_deactivation(self, db: Session, test_billing_rule: BillingRule):
        """Test deactivating a billing rule."""
        test_billing_rule.is_active = False
        db.commit()
        assert test_billing_rule.is_active is False


@pytest.mark.unit
@pytest.mark.db
class TestInvoiceLineItemModel:
    """Tests for InvoiceLineItem model."""

    def test_line_item_creation(self, test_invoice_line_item):
        """Test line item creation."""
        assert test_invoice_line_item.id is not None
        assert test_invoice_line_item.quantity == 10
        assert test_invoice_line_item.rate_cents == 150000
        assert test_invoice_line_item.amount_cents == 150000

    def test_line_item_quantity_variations(self, db: Session, test_invoice: Invoice):
        """Test line items with different quantities."""
        quantities = [1, 5, 10, 100]

        for qty in quantities:
            item = InvoiceLineItem(
                invoice_id=test_invoice.id,
                description=f"Item with {qty} units",
                quantity=qty,
                rate_cents=10000,
                amount_cents=qty * 10000,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(item)

        db.commit()
        assert len(test_invoice.line_items) >= len(quantities)


@pytest.mark.unit
@pytest.mark.db
class TestPaymentModel:
    """Tests for Payment model."""

    def test_payment_creation(self, test_payment):
        """Test payment creation."""
        assert test_payment.id is not None
        assert test_payment.amount_cents == 150000
        assert test_payment.payment_method == "bank_transfer"
        assert test_payment.status == "completed"

    def test_payment_status_lifecycle(self, db: Session, test_payment):
        """Test payment status transitions."""
        statuses = ["pending", "completed", "failed", "refunded"]

        for status in statuses:
            test_payment.status = status
            db.commit()
            assert test_payment.status == status

    def test_payment_relationship(self, test_payment, test_invoice: Invoice):
        """Test payment-invoice relationship."""
        assert test_payment.invoice_id == test_invoice.id
        assert len(test_invoice.payments) > 0
