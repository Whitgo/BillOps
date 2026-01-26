"""Celery tasks for email and Slack notifications."""
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.invoice import Invoice
from app.models.user import User
from app.services.invoices.generator import (
    render_invoice_html,
    generate_pdf_from_html,
    build_invoice_context,
)
from app.services.notifications.email import EmailNotificationService
from app.services.notifications.slack import SlackNotificationService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def send_invoice_email(
    self,
    invoice_id: str,
    recipient_email: str,
    recipient_name: str,
    layout: str = "professional",
) -> dict:
    """Send invoice via email.

    Args:
        invoice_id: UUID of Invoice
        recipient_email: Recipient email address
        recipient_name: Recipient name
        layout: Invoice template layout

    Returns:
        Dictionary with status
    """
    db = SessionLocal()
    try:
        invoice_uuid = UUID(invoice_id)
        invoice = db.query(Invoice).filter(Invoice.id == invoice_uuid).first()

        if not invoice:
            logger.error(f"Invoice {invoice_uuid} not found")
            return {"status": "error", "message": "Invoice not found"}

        # Build invoice context and generate HTML
        context = build_invoice_context(
            invoice=invoice,
            client=invoice.client,
            project=invoice.project,
            line_items=invoice.line_items,
        )

        html_content = render_invoice_html(context, layout)
        pdf_bytes = generate_pdf_from_html(html_content)

        # Send email
        email_service = EmailNotificationService()
        success = email_service.send_invoice_notification(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            invoice_number=invoice.invoice_number,
            invoice_total_cents=invoice.total_cents,
            invoice_html=html_content,
            invoice_pdf_bytes=pdf_bytes,
            due_date=invoice.due_date,
        )

        if success:
            logger.info(f"Invoice {invoice_uuid} email sent to {recipient_email}")
            return {
                "status": "success",
                "invoice_id": invoice_id,
                "recipient_email": recipient_email,
            }
        else:
            logger.error(f"Failed to send invoice email for {invoice_uuid}")
            return {
                "status": "error",
                "message": "Failed to send email",
                "invoice_id": invoice_id,
            }

    except Exception as exc:
        logger.error(f"Error sending invoice email: {exc}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def send_invoice_slack(
    self,
    invoice_id: str,
    slack_channel: str,
    include_details: bool = False,
) -> dict:
    """Send invoice notification to Slack.

    Args:
        invoice_id: UUID of Invoice
        slack_channel: Slack channel ID
        include_details: Include full details

    Returns:
        Dictionary with status
    """
    db = SessionLocal()
    try:
        invoice_uuid = UUID(invoice_id)
        invoice = db.query(Invoice).filter(Invoice.id == invoice_uuid).first()

        if not invoice:
            logger.error(f"Invoice {invoice_uuid} not found")
            return {"status": "error", "message": "Invoice not found"}

        slack_service = SlackNotificationService()

        if include_details:
            success = slack_service.send_invoice_details(
                channel=slack_channel,
                invoice_number=invoice.invoice_number,
                client_name=invoice.client.name,
                project_name=invoice.project.name if invoice.project else None,
                issue_date=invoice.issue_date.strftime("%B %d, %Y"),
                due_date=invoice.due_date.strftime("%B %d, %Y")
                if invoice.due_date
                else None,
                subtotal_cents=invoice.subtotal_cents,
                tax_cents=invoice.tax_cents,
                total_cents=invoice.total_cents,
                status=invoice.status,
            )
        else:
            success = slack_service.send_invoice_notification(
                channel=slack_channel,
                invoice_number=invoice.invoice_number,
                client_name=invoice.client.name,
                amount_cents=invoice.total_cents,
                status=invoice.status,
            )

        if success:
            logger.info(f"Invoice {invoice_uuid} notification sent to Slack")
            return {
                "status": "success",
                "invoice_id": invoice_id,
                "channel": slack_channel,
            }
        else:
            logger.error(f"Failed to send invoice Slack notification")
            return {
                "status": "error",
                "message": "Failed to send Slack message",
                "invoice_id": invoice_id,
            }

    except Exception as exc:
        logger.error(f"Error sending invoice Slack notification: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2)
def send_payment_email(
    self,
    invoice_id: str,
    payment_amount_cents: int,
    recipient_email: str,
    recipient_name: str,
) -> dict:
    """Send payment confirmation email.

    Args:
        invoice_id: UUID of Invoice
        payment_amount_cents: Payment amount in cents
        recipient_email: Recipient email address
        recipient_name: Recipient name

    Returns:
        Dictionary with status
    """
    db = SessionLocal()
    try:
        invoice_uuid = UUID(invoice_id)
        invoice = db.query(Invoice).filter(Invoice.id == invoice_uuid).first()

        if not invoice:
            logger.error(f"Invoice {invoice_uuid} not found")
            return {"status": "error", "message": "Invoice not found"}

        email_service = EmailNotificationService()
        success = email_service.send_payment_confirmation(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            invoice_number=invoice.invoice_number,
            payment_amount_cents=payment_amount_cents,
        )

        if success:
            logger.info(f"Payment confirmation email sent to {recipient_email}")
            return {
                "status": "success",
                "invoice_id": invoice_id,
                "recipient_email": recipient_email,
            }
        else:
            logger.error("Failed to send payment confirmation email")
            return {
                "status": "error",
                "message": "Failed to send email",
                "invoice_id": invoice_id,
            }

    except Exception as exc:
        logger.error(f"Error sending payment email: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2)
def send_payment_slack(
    self,
    invoice_id: str,
    payment_amount_cents: int,
    slack_channel: str,
) -> dict:
    """Send payment notification to Slack.

    Args:
        invoice_id: UUID of Invoice
        payment_amount_cents: Payment amount in cents
        slack_channel: Slack channel ID

    Returns:
        Dictionary with status
    """
    db = SessionLocal()
    try:
        invoice_uuid = UUID(invoice_id)
        invoice = db.query(Invoice).filter(Invoice.id == invoice_uuid).first()

        if not invoice:
            logger.error(f"Invoice {invoice_uuid} not found")
            return {"status": "error", "message": "Invoice not found"}

        slack_service = SlackNotificationService()
        success = slack_service.send_payment_notification(
            channel=slack_channel,
            invoice_number=invoice.invoice_number,
            client_name=invoice.client.name,
            amount_cents=payment_amount_cents,
        )

        if success:
            logger.info(f"Payment notification sent to Slack")
            return {
                "status": "success",
                "invoice_id": invoice_id,
                "channel": slack_channel,
            }
        else:
            logger.error("Failed to send payment Slack notification")
            return {
                "status": "error",
                "message": "Failed to send Slack message",
                "invoice_id": invoice_id,
            }

    except Exception as exc:
        logger.error(f"Error sending payment Slack notification: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2)
def send_overdue_invoice_alert(
    self,
    invoice_id: str,
    recipient_email: str,
    recipient_name: str,
    days_overdue: int,
    slack_channel: str | None = None,
) -> dict:
    """Send overdue invoice alert via email and optionally Slack.

    Args:
        invoice_id: UUID of Invoice
        recipient_email: Recipient email address
        recipient_name: Recipient name
        days_overdue: Days overdue
        slack_channel: Slack channel ID (optional)

    Returns:
        Dictionary with status
    """
    db = SessionLocal()
    try:
        invoice_uuid = UUID(invoice_id)
        invoice = db.query(Invoice).filter(Invoice.id == invoice_uuid).first()

        if not invoice:
            logger.error(f"Invoice {invoice_uuid} not found")
            return {"status": "error", "message": "Invoice not found"}

        results = {"email_sent": False, "slack_sent": False}

        # Send email alert
        email_service = EmailNotificationService()
        email_success = email_service.send_invoice_overdue_alert(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            invoice_number=invoice.invoice_number,
            invoice_total_cents=invoice.total_cents,
            days_overdue=days_overdue,
        )
        results["email_sent"] = email_success

        # Send Slack alert if channel provided
        if slack_channel:
            slack_service = SlackNotificationService()
            slack_success = slack_service.send_overdue_invoice_alert(
                channel=slack_channel,
                invoice_number=invoice.invoice_number,
                client_name=invoice.client.name,
                amount_cents=invoice.total_cents,
                days_overdue=days_overdue,
            )
            results["slack_sent"] = slack_success

        if results["email_sent"] or results["slack_sent"]:
            logger.info(f"Overdue alert sent for invoice {invoice_uuid}")
            return {
                "status": "success",
                "invoice_id": invoice_id,
                **results,
            }
        else:
            logger.error("Failed to send overdue alert")
            return {
                "status": "error",
                "message": "Failed to send alerts",
                "invoice_id": invoice_id,
            }

    except Exception as exc:
        logger.error(f"Error sending overdue alert: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task
def check_overdue_invoices() -> dict:
    """Check for overdue invoices and send alerts.

    Returns:
        Dictionary with results
    """
    db = SessionLocal()
    try:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        # Find overdue invoices
        overdue_invoices = db.query(Invoice).filter(
            Invoice.due_date < now,
            Invoice.status.in_(["sent", "partial"]),
        ).all()

        results = {
            "total_checked": len(overdue_invoices),
            "alerts_sent": 0,
            "failed": 0,
        }

        for invoice in overdue_invoices:
            days_overdue = (now - invoice.due_date).days

            # Send alert task
            task = send_overdue_invoice_alert.delay(
                invoice_id=str(invoice.id),
                recipient_email=invoice.client.email or "",
                recipient_name=invoice.client.name,
                days_overdue=days_overdue,
            )

            if task:
                results["alerts_sent"] += 1
            else:
                results["failed"] += 1

        logger.info(f"Overdue invoice check completed: {results}")
        return results

    except Exception as e:
        logger.error(f"Error checking overdue invoices: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

