"""Celery task for assembling time entries and generating invoice PDFs.

This module provides a Celery task that:
1. Collects approved time entries for a client/project within a period
2. Applies active billing rules to compute line items and totals
3. Renders invoice HTML with configurable template layouts
4. Generates a PDF document using WeasyPrint
5. Uploads the PDF to S3 storage
6. Updates the invoice record with PDF URL and metadata
7. Marks time entries as billed

Template layouts supported: 'minimalist', 'professional', 'branded'
Default layout: 'professional'
"""
from __future__ import annotations

import logging
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.celery_app import celery as celery_app
from app.db.session import SessionLocal
from app.models.invoice import Invoice
from app.models.invoice_line_item import InvoiceLineItem
from app.models.time_entry import TimeEntry
from app.models.client import Client
from app.models.project import Project
from app.services.billing_rule import BillingRuleService
from app.services.invoices.generator import generate_invoice_pdf, TEMPLATE_LAYOUTS
from app.services.storage.s3 import upload_to_s3

logger = logging.getLogger(__name__)


def _round_minutes(minutes: int, increment: int | None) -> int:
    if not increment or increment <= 0:
        return minutes
    return ((minutes + increment - 1) // increment) * increment


@celery_app.task(name="tasks.billing.generate_invoice", bind=True, max_retries=3)
def generate_invoice_task(
    self,
    invoice_id: str,
    template_layout: str = "professional",
    company_info: dict | None = None,
) -> dict:
    """Generate invoice PDF, upload to S3, and update invoice record.

    Assembles an invoice by:
    1. Retrieving the invoice and associated client/project
    2. Collecting approved time entries within optional period bounds
    3. Applying the active billing rule for the project
    4. Creating invoice line items with computed amounts
    5. Rendering HTML using the specified template layout
    6. Generating a PDF using WeasyPrint
    7. Uploading the PDF to S3
    8. Updating the invoice with PDF URL and marking time entries as billed

    Args:
        invoice_id: UUID string of the invoice to generate.
        template_layout: Invoice template layout. One of 'minimalist', 'professional', 
                        or 'branded'. Defaults to 'professional'.
        company_info: Optional dictionary with company metadata 
                     (name, email, address). If not provided, defaults are used.

    Returns:
        Dictionary with task result including:
        - status: 'success' or 'error'
        - invoice_id: Invoice UUID
        - invoice_number: Invoice number string
        - line_items: Number of line items created
        - subtotal_cents: Subtotal amount in cents
        - total_cents: Total amount including tax in cents
        - pdf_url: S3 URL of generated PDF (if successful)
        - message: Error message if status is 'error'

    Raises:
        Will retry up to 3 times on failure with exponential backoff.
    """
    db: Session = SessionLocal()
    try:
        # Validate template layout
        if template_layout not in TEMPLATE_LAYOUTS:
            logger.warning(f"Unknown template layout '{template_layout}', using 'professional'")
            template_layout = "professional"

        inv_id = UUID(invoice_id)
        invoice: Invoice | None = db.query(Invoice).filter(Invoice.id == inv_id).first()
        if not invoice:
            return {"status": "error", "message": f"Invoice {invoice_id} not found"}

        client: Client | None = db.query(Client).filter(Client.id == invoice.client_id).first()
        project: Project | None = None
        if invoice.project_id:
            project = db.query(Project).filter(Project.id == invoice.project_id).first()

        # Determine period from meta (optional)
        period_start = None
        period_end = None
        if invoice.meta and isinstance(invoice.meta, dict):
            ps = invoice.meta.get("period_start")
            pe = invoice.meta.get("period_end")
            try:
                period_start = datetime.fromisoformat(ps) if ps else None
                period_end = datetime.fromisoformat(pe) if pe else None
            except Exception:
                period_start = None
                period_end = None

        # Collect approved time entries
        q = db.query(TimeEntry).filter(
            TimeEntry.client_id == invoice.client_id,
            TimeEntry.status == "approved",
        )
        if invoice.project_id:
            q = q.filter(TimeEntry.project_id == invoice.project_id)
        if period_start:
            q = q.filter(TimeEntry.started_at >= period_start)
        if period_end:
            q = q.filter(TimeEntry.ended_at <= period_end)

        entries: list[TimeEntry] = q.order_by(TimeEntry.started_at.asc()).all()
        if not entries:
            return {"status": "error", "message": "No approved time entries found for invoice"}

        # Apply billing rules and create line items
        rule = None
        if project:
            rule = BillingRuleService.get_active_for_project(db, project.id)

        line_items: list[InvoiceLineItem] = []
        subtotal_cents = 0

        for te in entries:
            # Determine rate
            rate_cents = rule.rate_cents if rule else 0
            increment = rule.rounding_increment_minutes if rule else 0

            billable_minutes = _round_minutes(te.duration_minutes, increment)
            qty_hours = billable_minutes / 60.0
            amount_cents = int(round(qty_hours * (rate_cents or 0)))

            li = InvoiceLineItem(
                invoice_id=invoice.id,
                time_entry_id=te.id,
                description=te.description or "Work",
                quantity=f"{qty_hours:.2f} h",
                unit_price_cents=rate_cents or 0,
                amount_cents=amount_cents,
                billing_rule_snapshot={
                    "rule_id": str(rule.id) if rule else None,
                    "rule_type": getattr(rule, "rule_type", None),
                    "rate_cents": rate_cents or 0,
                    "increment_minutes": increment or 0,
                },
            )
            line_items.append(li)
            subtotal_cents += amount_cents
            db.add(li)

            # Mark time entry as billed and attach rule
            te.status = "billed"
            if rule:
                te.billing_rule_id = rule.id
            db.add(te)

        # Update invoice totals
        invoice.subtotal_cents = subtotal_cents
        invoice.tax_cents = invoice.tax_cents or 0
        invoice.total_cents = (invoice.subtotal_cents or 0) + (invoice.tax_cents or 0)
        invoice.updated_at = datetime.now(timezone.utc)
        db.add(invoice)
        db.flush()

        # Generate PDF with specified layout
        try:
            pdf_bytes = generate_invoice_pdf(
                invoice,
                client,
                project,
                line_items,
                company_info=company_info,
                layout=template_layout,
            )
            logger.info(f"Generated PDF for invoice {invoice.invoice_number} using '{template_layout}' layout")
        except Exception as e:
            logger.error(f"Failed to generate PDF for invoice {invoice.invoice_number}: {e}")
            raise

        # Upload to S3
        file_key = f"invoices/{invoice.invoice_number}.pdf"
        pdf_url = upload_to_s3(pdf_bytes, file_key, content_type="application/pdf")

        # Update invoice meta and status
        meta = (invoice.meta or {})
        if pdf_url:
            meta["pdf_url"] = pdf_url
            logger.info(f"PDF uploaded to S3: {pdf_url}")
        else:
            logger.warning(f"PDF was not uploaded to S3 (S3 may not be configured)")
        meta["generated_at"] = datetime.now(timezone.utc).isoformat()
        meta["template_layout"] = template_layout
        invoice.meta = meta
        invoice.status = "sent"
        invoice.updated_at = datetime.now(timezone.utc)
        db.add(invoice)

        db.commit()

        return {
            "status": "success",
            "invoice_id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "line_items": len(line_items),
            "subtotal_cents": subtotal_cents,
            "total_cents": invoice.total_cents,
            "pdf_url": pdf_url,
            "template_layout": template_layout,
        }

    except Exception as e:
        logger.error(f"Error in generate_invoice_task: {e}", exc_info=True)
        try:
            self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except Exception:
            return {"status": "error", "message": str(e), "retried": True}
    finally:
        db.close()
