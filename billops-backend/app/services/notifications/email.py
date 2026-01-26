"""Email notification service integration."""
import logging
from typing import Any
from datetime import datetime

from app.services.email import EmailService
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending email notifications."""

    def __init__(self):
        self.email_service = EmailService()
        self.settings = get_settings()

    def send_invoice_notification(
        self,
        recipient_email: str,
        recipient_name: str,
        invoice_number: str,
        invoice_total_cents: int,
        invoice_html: str,
        invoice_pdf_bytes: bytes | None = None,
        due_date: datetime | None = None,
    ) -> bool:
        """Send invoice notification email.

        Args:
            recipient_email: Recipient email address
            recipient_name: Recipient name
            invoice_number: Invoice number
            invoice_total_cents: Invoice total in cents
            invoice_html: HTML invoice content
            invoice_pdf_bytes: PDF invoice bytes (optional)
            due_date: Invoice due date (optional)

        Returns:
            True if sent successfully
        """
        try:
            invoice_total = invoice_total_cents / 100
            due_date_str = None
            if due_date:
                due_date_str = due_date.strftime("%B %d, %Y")

            return self.email_service.send_invoice_email(
                to_email=recipient_email,
                client_name=recipient_name,
                invoice_number=invoice_number,
                invoice_total=invoice_total,
                html_content=invoice_html,
                pdf_bytes=invoice_pdf_bytes,
                due_date=due_date_str,
            )
        except Exception as e:
            logger.error(f"Failed to send invoice notification: {e}", exc_info=True)
            return False

    def send_payment_confirmation(
        self,
        recipient_email: str,
        recipient_name: str,
        invoice_number: str,
        payment_amount_cents: int,
        payment_date: datetime | None = None,
    ) -> bool:
        """Send payment confirmation email.

        Args:
            recipient_email: Recipient email address
            recipient_name: Recipient name
            invoice_number: Invoice number
            payment_amount_cents: Payment amount in cents
            payment_date: Payment date (optional)

        Returns:
            True if sent successfully
        """
        try:
            payment_amount = payment_amount_cents / 100
            payment_date_str = (
                payment_date.strftime("%B %d, %Y") if payment_date else "today"
            )

            message = (
                f"Dear {recipient_name},\n\n"
                f"Thank you for your payment of ${payment_amount:,.2f} on {payment_date_str} "
                f"toward Invoice {invoice_number}.\n\n"
                f"Your payment has been recorded.\n\n"
                f"Best regards,\nBillOps"
            )

            return self.email_service.send_alert_email(
                to_email=recipient_email,
                alert_title="Payment Confirmation",
                alert_message=message,
                alert_type="success",
            )
        except Exception as e:
            logger.error(f"Failed to send payment confirmation: {e}", exc_info=True)
            return False

    def send_invoice_overdue_alert(
        self,
        recipient_email: str,
        recipient_name: str,
        invoice_number: str,
        invoice_total_cents: int,
        days_overdue: int,
    ) -> bool:
        """Send invoice overdue alert email.

        Args:
            recipient_email: Recipient email address
            recipient_name: Recipient name
            invoice_number: Invoice number
            invoice_total_cents: Invoice total in cents
            days_overdue: Number of days overdue

        Returns:
            True if sent successfully
        """
        try:
            invoice_total = invoice_total_cents / 100
            message = (
                f"Dear {recipient_name},\n\n"
                f"Invoice {invoice_number} for ${invoice_total:,.2f} is now {days_overdue} days overdue.\n\n"
                f"Please submit payment at your earliest convenience.\n\n"
                f"Best regards,\nBillOps"
            )

            return self.email_service.send_alert_email(
                to_email=recipient_email,
                alert_title="Invoice Overdue",
                alert_message=message,
                alert_type="warning",
            )
        except Exception as e:
            logger.error(f"Failed to send overdue alert: {e}", exc_info=True)
            return False

    def send_time_entry_reminder(
        self,
        recipient_email: str,
        recipient_name: str,
        total_hours: float,
        entry_count: int,
    ) -> bool:
        """Send time entry reminder email.

        Args:
            recipient_email: Recipient email address
            recipient_name: Recipient name
            total_hours: Total hours logged today
            entry_count: Number of time entries

        Returns:
            True if sent successfully
        """
        try:
            message = (
                f"Dear {recipient_name},\n\n"
                f"Daily reminder: You have logged {entry_count} time entries "
                f"totaling {total_hours:.1f} hours today.\n\n"
                f"Best regards,\nBillOps"
            )

            return self.email_service.send_alert_email(
                to_email=recipient_email,
                alert_title="Time Entry Summary",
                alert_message=message,
                alert_type="info",
            )
        except Exception as e:
            logger.error(f"Failed to send time entry reminder: {e}", exc_info=True)
            return False

