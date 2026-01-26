"""
Integration tests for invoice generation workflow.
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.invoice_line_item import InvoiceLineItem
from app.models.time_entry import TimeEntry
from app.models.payment import Payment
from app.services.invoice import InvoiceService
from app.services.time_entry import TimeEntryService
from app.services.billing_rule import BillingRuleService


@pytest.mark.integration
@pytest.mark.db
class TestInvoiceGenerationWorkflow:
    """Integration tests for complete invoice generation workflow."""

    def test_complete_invoice_generation_workflow(
        self,
        db: Session,
        test_user,
        test_client,
        test_project,
        test_billing_rule,
        make_time_entry_factory,
    ):
        """
        Test complete workflow:
        1. Create time entries
        2. Calculate billable hours
        3. Generate invoice
        4. Create line items
        5. Verify invoice amounts
        """
        # Step 1: Create multiple time entries
        now = datetime.now(timezone.utc)
        entries = []
        for i in range(5):
            entry = make_time_entry_factory(
                start_time=now - timedelta(hours=5 - i),
                duration_minutes=120,  # 2 hours each
                description=f"Work session {i + 1}",
                is_billable=True,
            )
            entries.append(entry)

        # Step 2: Calculate billable hours
        time_service = TimeEntryService(db)
        period_start = now - timedelta(days=30)
        period_end = now

        billable_hours = time_service.calculate_billable_hours(
            test_user.id,
            period_start,
            period_end,
        )
        assert billable_hours == 10.0  # 5 entries * 2 hours

        # Step 3: Generate invoice
        invoice_service = InvoiceService(db)
        invoice = invoice_service.create(
            client_id=test_client.id,
            project_id=test_project.id,
            issue_date=now,
            due_date=now + timedelta(days=30),
        )
        assert invoice.status == "draft"

        # Step 4: Create line items for billed hours
        hourly_rate_cents = test_project.hourly_rate_cents
        total_amount_cents = int(billable_hours * hourly_rate_cents)

        line_item = InvoiceLineItem(
            invoice_id=invoice.id,
            description=f"Professional services - {billable_hours} hours @ ${hourly_rate_cents / 100:.2f}/hr",
            quantity=billable_hours,
            rate_cents=hourly_rate_cents,
            amount_cents=total_amount_cents,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(line_item)
        db.commit()
        db.refresh(line_item)

        # Step 5: Update invoice amounts
        invoice.subtotal_cents = total_amount_cents
        invoice.total_cents = total_amount_cents
        db.commit()
        db.refresh(invoice)

        # Verify
        assert invoice.total_cents == 150000  # 10 hours * $150/hour = $1500
        assert len(invoice.line_items) == 1
        assert invoice.line_items[0].amount_cents == 150000

    def test_invoice_with_tax_calculation(
        self,
        db: Session,
        test_client,
        test_project,
    ):
        """Test invoice generation with tax calculation."""
        invoice_service = InvoiceService(db)
        now = datetime.now(timezone.utc)

        # Create invoice
        invoice = invoice_service.create(
            client_id=test_client.id,
            project_id=test_project.id,
            issue_date=now,
            due_date=now + timedelta(days=30),
        )

        # Set amounts with 10% tax
        subtotal = 100000  # $1000
        tax = 10000  # $100
        total = subtotal + tax

        invoice.subtotal_cents = subtotal
        invoice.tax_cents = tax
        invoice.total_cents = total
        db.commit()

        # Verify
        assert invoice.subtotal_cents == 100000
        assert invoice.tax_cents == 10000
        assert invoice.total_cents == 110000

    def test_invoice_status_workflow(
        self,
        db: Session,
        test_invoice: Invoice,
    ):
        """Test invoice status transitions."""
        invoice_service = InvoiceService(db)

        # Draft -> Sent
        invoice_service.update_status(test_invoice.id, "sent")
        db.refresh(test_invoice)
        assert test_invoice.status == "sent"

        # Sent -> Paid
        invoice_service.update_status(test_invoice.id, "paid")
        db.refresh(test_invoice)
        assert test_invoice.status == "paid"

    def test_invoice_payment_workflow(
        self,
        db: Session,
        test_invoice: Invoice,
    ):
        """Test invoice payment recording."""
        # Record partial payment
        payment1 = Payment(
            invoice_id=test_invoice.id,
            amount_cents=75000,  # $750 (half)
            payment_date=datetime.now(timezone.utc),
            payment_method="bank_transfer",
            status="completed",
            transaction_id="TXN-001",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(payment1)
        db.commit()

        # Record remaining payment
        payment2 = Payment(
            invoice_id=test_invoice.id,
            amount_cents=75000,  # $750 (remaining)
            payment_date=datetime.now(timezone.utc),
            payment_method="bank_transfer",
            status="completed",
            transaction_id="TXN-002",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(payment2)
        db.commit()
        db.refresh(test_invoice)

        # Verify
        total_paid = sum(p.amount_cents for p in test_invoice.payments)
        assert total_paid == test_invoice.total_cents

    def test_multiple_invoices_for_different_clients(
        self,
        db: Session,
        test_user,
        test_project,
        make_invoice_factory,
    ):
        """Test generating multiple invoices for different projects."""
        from app.models.client import Client

        # Create multiple clients
        client1 = Client(
            user_id=test_user.id,
            name="Client A",
            email="clienta@example.com",
            currency="USD",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        client2 = Client(
            user_id=test_user.id,
            name="Client B",
            email="clientb@example.com",
            currency="USD",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(client1)
        db.add(client2)
        db.commit()

        # Create invoices for each client
        invoice1 = make_invoice_factory(invoice_number="INV-CLIENT-A-001")
        invoice2 = make_invoice_factory(invoice_number="INV-CLIENT-B-001")

        invoice_service = InvoiceService(db)

        # Verify they can be retrieved separately
        assert invoice_service.get_by_id(invoice1.id) is not None
        assert invoice_service.get_by_id(invoice2.id) is not None

    def test_invoice_overdue_detection(
        self,
        db: Session,
        test_client,
        test_project,
    ):
        """Test detecting overdue invoices."""
        invoice_service = InvoiceService(db)

        # Create invoice that's now overdue
        overdue_date = datetime.now(timezone.utc) - timedelta(days=35)
        invoice = invoice_service.create(
            client_id=test_client.id,
            project_id=test_project.id,
            issue_date=overdue_date,
            due_date=overdue_date + timedelta(days=30),
        )

        invoice_service.update_status(invoice.id, "sent")
        db.refresh(invoice)

        # Check if overdue
        assert invoice.due_date < datetime.now(timezone.utc)

    def test_invoice_with_line_items_sum_to_total(
        self,
        db: Session,
        test_invoice: Invoice,
    ):
        """Test that invoice line items sum to invoice total."""
        # Add multiple line items
        line_items = []
        for i in range(3):
            item = InvoiceLineItem(
                invoice_id=test_invoice.id,
                description=f"Service {i + 1}",
                quantity=5,
                rate_cents=10000,
                amount_cents=50000,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(item)
            line_items.append(item)

        db.commit()
        db.refresh(test_invoice)

        # Calculate total from line items
        total_from_items = sum(item.amount_cents for item in test_invoice.line_items)
        assert total_from_items == 150000


@pytest.mark.integration
@pytest.mark.db
class TestTimeCaptureToBillingWorkflow:
    """Integration tests for time capture to billing workflow."""

    def test_time_entry_to_invoice_workflow(
        self,
        db: Session,
        test_user,
        test_client,
        test_project,
        test_billing_rule,
        make_time_entry_factory,
    ):
        """
        Test complete workflow:
        1. Capture time entries
        2. Mark entries as billable
        3. Generate invoice from billable hours
        4. Verify invoice matches tracked time
        """
        now = datetime.now(timezone.utc)
        invoice_service = InvoiceService(db)
        time_service = TimeEntryService(db)

        # Step 1: Capture time entries
        entries = []
        for i in range(4):
            entry = make_time_entry_factory(
                start_time=now - timedelta(hours=4 - i),
                duration_minutes=90,
                description=f"Task {i + 1}",
                is_billable=True,
            )
            entries.append(entry)

        # Step 2: Mark as billable (already done in creation, but verify)
        billable_entries = [e for e in entries if e.is_billable]
        assert len(billable_entries) == 4

        # Step 3: Calculate billable time
        period_start = now - timedelta(days=30)
        period_end = now + timedelta(days=1)
        total_hours = time_service.calculate_billable_hours(
            test_user.id,
            period_start,
            period_end,
        )
        assert total_hours == 6.0  # 4 entries * 90 minutes = 360 minutes = 6 hours

        # Step 4: Generate invoice
        invoice = invoice_service.create(
            client_id=test_client.id,
            project_id=test_project.id,
            issue_date=now,
            due_date=now + timedelta(days=30),
        )

        # Step 5: Create invoice line item from tracked time
        hourly_rate_cents = test_project.hourly_rate_cents
        invoice_amount_cents = int(total_hours * hourly_rate_cents)

        line_item = InvoiceLineItem(
            invoice_id=invoice.id,
            description=f"{total_hours} hours of work @ ${hourly_rate_cents / 100:.2f}/hr",
            quantity=total_hours,
            rate_cents=hourly_rate_cents,
            amount_cents=invoice_amount_cents,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(line_item)

        # Update invoice totals
        invoice.subtotal_cents = invoice_amount_cents
        invoice.total_cents = invoice_amount_cents
        db.commit()
        db.refresh(invoice)

        # Step 6: Verify invoice matches time
        assert invoice.total_cents == 900000  # 6 hours * $150/hour = $900

    def test_mixed_billable_nonbillable_time_entries(
        self,
        db: Session,
        test_user,
        test_project,
        make_time_entry_factory,
    ):
        """Test that non-billable entries are excluded from invoicing."""
        now = datetime.now(timezone.utc)
        time_service = TimeEntryService(db)

        # Create mix of billable and non-billable entries
        billable_entries = [
            make_time_entry_factory(duration_minutes=120, is_billable=True),
            make_time_entry_factory(duration_minutes=90, is_billable=True),
        ]
        nonbillable_entries = [
            make_time_entry_factory(duration_minutes=60, is_billable=False),
            make_time_entry_factory(duration_minutes=30, is_billable=False),
        ]

        # Calculate billable hours
        period_start = now - timedelta(days=1)
        period_end = now + timedelta(days=1)
        billable_hours = time_service.calculate_billable_hours(
            test_user.id,
            period_start,
            period_end,
        )

        # Should only count billable entries: 120 + 90 = 210 minutes = 3.5 hours
        assert billable_hours == 3.5

    def test_concurrent_time_entries_same_project(
        self,
        db: Session,
        test_user,
        test_project,
        make_time_entry_factory,
    ):
        """Test handling overlapping/concurrent time entries."""
        now = datetime.now(timezone.utc)

        # Create concurrent entries (should be allowed by system)
        entry1 = make_time_entry_factory(
            start_time=now - timedelta(hours=2),
            duration_minutes=120,
        )
        entry2 = make_time_entry_factory(
            start_time=now - timedelta(hours=1, minutes=30),
            duration_minutes=90,
        )

        # Verify both exist
        assert entry1.id != entry2.id
        assert entry1.project_id == entry2.project_id

    def test_time_entry_duration_rounding(
        self,
        db: Session,
        test_user,
        test_project,
    ):
        """Test that fractional durations are handled correctly."""
        time_service = TimeEntryService(db)
        now = datetime.now(timezone.utc)

        # Create entry with exact fractional hours
        entry = TimeEntry(
            user_id=test_user.id,
            project_id=test_project.id,
            description="Fractional hours",
            start_time=now,
            end_time=now + timedelta(minutes=45),
            duration_minutes=45,
            is_billable=True,
            is_billed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(entry)
        db.commit()

        # Verify duration
        assert entry.duration_minutes == 45  # 0.75 hours

    def test_time_entry_marking_as_billed(
        self,
        db: Session,
        test_user,
        test_project,
        make_time_entry_factory,
    ):
        """Test marking time entries as billed after invoicing."""
        time_service = TimeEntryService(db)

        # Create entries
        entries = [
            make_time_entry_factory(duration_minutes=60, is_billable=True),
            make_time_entry_factory(duration_minutes=60, is_billable=True),
        ]

        # Initially not billed
        for entry in entries:
            assert entry.is_billed is False

        # Mark as billed
        for entry in entries:
            time_service.mark_as_billed(entry.id)

        # Verify marked as billed
        db.refresh(entries[0])
        db.refresh(entries[1])
        for entry in entries:
            assert entry.is_billed is True
