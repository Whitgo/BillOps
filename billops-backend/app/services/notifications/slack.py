"""Slack notification service integration."""
import logging
from typing import Any
from datetime import datetime, timezone

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from app.config.settings import get_settings
from app.services.slack_message_formatter import (
    format_invoice_message,
    format_payment_message,
    format_time_entry_message,
    format_daily_summary_message,
    format_alert_message,
    format_overdue_invoice_alert,
    format_invoice_details_message,
)

logger = logging.getLogger(__name__)


class SlackNotificationService:
    """Service for sending Slack notifications with rich formatting."""

    def __init__(self, bot_token: str | None = None):
        self.settings = get_settings()
        self.bot_token = bot_token or self.settings.slack_bot_token
        self.client = WebClient(token=self.bot_token) if self.bot_token else None

    def send_message(
        self,
        channel: str,
        message: dict[str, Any],
        thread_ts: str | None = None,
    ) -> bool:
        """Send formatted message to Slack channel.

        Args:
            channel: Channel ID or name
            message: Message dict with blocks
            thread_ts: Thread timestamp for threading

        Returns:
            True if successful
        """
        if not self.client:
            logger.error("Slack client not configured")
            return False

        try:
            self.client.chat_postMessage(
                channel=channel,
                **message,
                thread_ts=thread_ts,
            )
            logger.info(f"Message sent to {channel}")
            return True
        except SlackApiError as e:
            logger.error(f"Failed to send message to {channel}: {e}")
            return False

    def send_invoice_notification(
        self,
        channel: str,
        invoice_number: str,
        client_name: str,
        amount_cents: int,
        status: str = "sent",
    ) -> bool:
        """Send invoice notification.

        Args:
            channel: Channel ID or name
            invoice_number: Invoice number
            client_name: Client name
            amount_cents: Amount in cents
            status: Invoice status

        Returns:
            True if successful
        """
        try:
            amount = amount_cents / 100
            message = format_invoice_message(
                invoice_number=invoice_number,
                client_name=client_name,
                amount=amount,
                status=status,
            )
            return self.send_message(channel, message)
        except Exception as e:
            logger.error(f"Failed to send invoice notification: {e}")
            return False

    def send_payment_notification(
        self,
        channel: str,
        invoice_number: str,
        client_name: str,
        amount_cents: int,
    ) -> bool:
        """Send payment received notification.

        Args:
            channel: Channel ID or name
            invoice_number: Invoice number
            client_name: Client name
            amount_cents: Payment amount in cents

        Returns:
            True if successful
        """
        try:
            amount = amount_cents / 100
            message = format_payment_message(
                invoice_number=invoice_number,
                client_name=client_name,
                amount=amount,
            )
            return self.send_message(channel, message)
        except Exception as e:
            logger.error(f"Failed to send payment notification: {e}")
            return False

    def send_time_entry_notification(
        self,
        channel: str,
        description: str,
        duration_minutes: int,
        project_name: str | None = None,
        client_name: str | None = None,
    ) -> bool:
        """Send time entry notification.

        Args:
            channel: Channel ID or name
            description: Entry description
            duration_minutes: Duration in minutes
            project_name: Project name (optional)
            client_name: Client name (optional)

        Returns:
            True if successful
        """
        try:
            duration_hours = duration_minutes / 60
            message = format_time_entry_message(
                description=description,
                duration_hours=duration_hours,
                project_name=project_name,
                client_name=client_name,
            )
            return self.send_message(channel, message)
        except Exception as e:
            logger.error(f"Failed to send time entry notification: {e}")
            return False

    def send_daily_summary(
        self,
        channel: str,
        total_hours: float,
        entry_count: int,
        date_str: str | None = None,
    ) -> bool:
        """Send daily summary notification.

        Args:
            channel: Channel ID or name
            total_hours: Total hours worked
            entry_count: Number of entries
            date_str: Date string (optional)

        Returns:
            True if successful
        """
        try:
            message = format_daily_summary_message(
                total_hours=total_hours,
                entry_count=entry_count,
                date_str=date_str,
            )
            return self.send_message(channel, message)
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
            return False

    def send_alert(
        self,
        channel: str,
        title: str,
        message: str,
        alert_type: str = "info",
    ) -> bool:
        """Send alert notification.

        Args:
            channel: Channel ID or name
            title: Alert title
            message: Alert message
            alert_type: Alert type (info, warning, error, success)

        Returns:
            True if successful
        """
        try:
            msg = format_alert_message(
                title=title,
                message=message,
                alert_type=alert_type,
            )
            return self.send_message(channel, msg)
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False

    def send_overdue_invoice_alert(
        self,
        channel: str,
        invoice_number: str,
        client_name: str,
        amount_cents: int,
        days_overdue: int,
    ) -> bool:
        """Send overdue invoice alert.

        Args:
            channel: Channel ID or name
            invoice_number: Invoice number
            client_name: Client name
            amount_cents: Invoice amount in cents
            days_overdue: Days overdue

        Returns:
            True if successful
        """
        try:
            amount = amount_cents / 100
            message = format_overdue_invoice_alert(
                invoice_number=invoice_number,
                client_name=client_name,
                amount=amount,
                days_overdue=days_overdue,
            )
            return self.send_message(channel, message)
        except Exception as e:
            logger.error(f"Failed to send overdue alert: {e}")
            return False

    def send_invoice_details(
        self,
        channel: str,
        invoice_number: str,
        client_name: str,
        project_name: str | None,
        issue_date: str,
        due_date: str | None,
        subtotal_cents: int,
        tax_cents: int,
        total_cents: int,
        status: str = "draft",
    ) -> bool:
        """Send detailed invoice message.

        Args:
            channel: Channel ID or name
            invoice_number: Invoice number
            client_name: Client name
            project_name: Project name (optional)
            issue_date: Issue date string
            due_date: Due date string (optional)
            subtotal_cents: Subtotal in cents
            tax_cents: Tax in cents
            total_cents: Total in cents
            status: Invoice status

        Returns:
            True if successful
        """
        try:
            subtotal = subtotal_cents / 100
            tax = tax_cents / 100
            total = total_cents / 100

            message = format_invoice_details_message(
                invoice_number=invoice_number,
                client_name=client_name,
                project_name=project_name,
                issue_date=issue_date,
                due_date=due_date,
                subtotal=subtotal,
                tax=tax,
                total=total,
                status=status,
            )
            return self.send_message(channel, message)
        except Exception as e:
            logger.error(f"Failed to send invoice details: {e}")
            return False

