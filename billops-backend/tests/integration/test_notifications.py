"""Tests for email and Slack notification services."""
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.user import User
from app.models.client import Client
from app.services.email import EmailService, SendGridEmailProvider, AWSEmailProvider
from app.services.email_templates import EmailTemplates
from app.services.notifications.email import EmailNotificationService
from app.services.notifications.slack import SlackNotificationService
from app.services.slack_message_formatter import (
    SlackMessageBuilder,
    format_invoice_message,
    format_payment_message,
    format_daily_summary_message,
)


class TestEmailService:
    """Tests for email service providers."""

    def test_sendgrid_email_provider_initialization(self, monkeypatch):
        """Test SendGrid provider initialization."""
        monkeypatch.setenv("EMAIL_PROVIDER", "sendgrid")
        monkeypatch.setenv("SENDGRID_API_KEY", "test_key_123")
        monkeypatch.setenv("FROM_EMAIL", "test@billops.com")
        monkeypatch.setenv("FROM_NAME", "BillOps")

        with patch("app.services.email.SendGridAPIClient"):
            provider = SendGridEmailProvider()
            assert provider.settings.sendgrid_api_key == "test_key_123"

    def test_send_email_via_sendgrid(self, monkeypatch):
        """Test sending email via SendGrid."""
        monkeypatch.setenv("EMAIL_PROVIDER", "sendgrid")
        monkeypatch.setenv("SENDGRID_API_KEY", "test_key_123")
        monkeypatch.setenv("FROM_EMAIL", "test@billops.com")
        monkeypatch.setenv("FROM_NAME", "BillOps")

        with patch("app.services.email.SendGridAPIClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_client_instance = MagicMock()
            mock_client_instance.send.return_value = mock_response
            mock_client.return_value = mock_client_instance

            with patch("app.services.email.Mail"), \
                 patch("app.services.email.Email"), \
                 patch("app.services.email.To"), \
                 patch("app.services.email.Content"):

                provider = SendGridEmailProvider()
                success = provider.send_email(
                    to_email="client@example.com",
                    subject="Test Email",
                    html_content="<h1>Test</h1>",
                )

                assert success is True

    def test_aws_email_provider_initialization(self, monkeypatch):
        """Test AWS SES provider initialization."""
        monkeypatch.setenv("EMAIL_PROVIDER", "ses")
        monkeypatch.setenv("SES_ACCESS_KEY_ID", "test_key")
        monkeypatch.setenv("SES_SECRET_ACCESS_KEY", "test_secret")
        monkeypatch.setenv("FROM_EMAIL", "test@billops.com")

        with patch("app.services.email.boto3"):
            provider = AWSEmailProvider()
            assert provider.settings.ses_access_key_id == "test_key"

    def test_email_service_provider_selection(self, monkeypatch):
        """Test EmailService selects correct provider."""
        monkeypatch.setenv("EMAIL_PROVIDER", "sendgrid")
        monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
        monkeypatch.setenv("FROM_EMAIL", "test@billops.com")

        with patch("app.services.email.SendGridEmailProvider") as mock_sendgrid:
            EmailService()
            mock_sendgrid.assert_called_once()

    def test_email_send_with_attachments(self, monkeypatch):
        """Test sending email with PDF attachment."""
        monkeypatch.setenv("EMAIL_PROVIDER", "sendgrid")
        monkeypatch.setenv("SENDGRID_API_KEY", "test_key_123")
        monkeypatch.setenv("FROM_EMAIL", "test@billops.com")

        pdf_content = b"%PDF-1.4 fake pdf"

        with patch("app.services.email.SendGridAPIClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_client_instance = MagicMock()
            mock_client_instance.send.return_value = mock_response
            mock_client.return_value = mock_client_instance

            with patch("app.services.email.Mail"), \
                 patch("app.services.email.Email"), \
                 patch("app.services.email.To"), \
                 patch("app.services.email.Content"):

                provider = SendGridEmailProvider()
                success = provider.send_email(
                    to_email="client@example.com",
                    subject="Invoice with Attachment",
                    html_content="<h1>Invoice</h1>",
                    attachments={"invoice.pdf": pdf_content},
                )

                assert success is True


class TestEmailTemplates:
    """Tests for email template generators."""

    def test_invoice_template_generation(self):
        """Test invoice email template generation."""
        invoice_date = datetime(2024, 1, 15)
        due_date = datetime(2024, 2, 15)

        templates = EmailTemplates.invoice_template(
            client_name="Acme Corp",
            invoice_number="INV-2024-001",
            invoice_date=invoice_date,
            due_date=due_date,
            total_amount=1500.00,
            currency="USD",
        )

        assert "html" in templates
        assert "text" in templates
        assert "INV-2024-001" in templates["html"]
        assert "1,500.00" in templates["html"]
        assert "Acme Corp" in templates["html"]

    def test_invoice_template_with_items(self):
        """Test invoice template with line items."""
        invoice_date = datetime(2024, 1, 15)

        items = [
            {"description": "Web Development", "quantity": 40, "rate": 150},
            {"description": "Consulting", "quantity": 10, "rate": 200},
        ]

        templates = EmailTemplates.invoice_template(
            client_name="Tech Client",
            invoice_number="INV-001",
            invoice_date=invoice_date,
            due_date=None,
            total_amount=8000.00,
            items=items,
        )

        assert "Web Development" in templates["html"]
        assert "40" in templates["html"]
        assert "150" in templates["html"]

    def test_payment_confirmation_template(self):
        """Test payment confirmation email template."""
        payment_date = datetime(2024, 1, 20)

        templates = EmailTemplates.payment_confirmation_template(
            client_name="Acme Corp",
            invoice_number="INV-2024-001",
            payment_amount=1500.00,
            payment_date=payment_date,
        )

        assert "html" in templates
        assert "text" in templates
        assert "Payment Received" in templates["html"]
        assert "1,500.00" in templates["html"]
        assert "INV-2024-001" in templates["html"]

    def test_overdue_invoice_template(self):
        """Test overdue invoice email template."""
        due_date = datetime(2024, 1, 1)

        templates = EmailTemplates.overdue_invoice_template(
            client_name="Late Payer",
            invoice_number="INV-2024-001",
            amount_due=2000.00,
            days_overdue=15,
            due_date=due_date,
        )

        assert "html" in templates
        assert "Overdue" in templates["html"]
        assert "15 days" in templates["html"]
        assert "2,000.00" in templates["html"]

    def test_time_entry_summary_template(self):
        """Test time entry summary email template."""
        summary_date = datetime(2024, 1, 15)
        entries = [
            {"description": "Client Meeting", "hours": 2.5},
            {"description": "Development", "hours": 4.0},
            {"description": "Code Review", "hours": 1.0},
        ]

        templates = EmailTemplates.time_entry_summary_template(
            user_name="John Doe",
            summary_date=summary_date,
            total_hours=7.5,
            entry_count=3,
            entries=entries,
        )

        assert "html" in templates
        assert "text" in templates
        assert "Daily Time Summary" in templates["html"]
        assert "7.5" in templates["html"]
        assert "Client Meeting" in templates["html"]


class TestEmailNotificationService:
    """Tests for email notification service."""

    def test_send_invoice_notification(self, monkeypatch):
        """Test sending invoice notification."""
        monkeypatch.setenv("EMAIL_PROVIDER", "sendgrid")
        monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
        monkeypatch.setenv("FROM_EMAIL", "test@billops.com")

        service = EmailNotificationService()

        with patch.object(service.email_service, "send_invoice_email") as mock_send:
            mock_send.return_value = True

            success = service.send_invoice_notification(
                recipient_email="client@example.com",
                recipient_name="Acme Corp",
                invoice_number="INV-001",
                invoice_total_cents=150000,
                invoice_html="<h1>Invoice</h1>",
                due_date=datetime.now(timezone.utc) + timedelta(days=30),
            )

            assert success is True
            mock_send.assert_called_once()

    def test_send_payment_confirmation(self, monkeypatch):
        """Test sending payment confirmation."""
        monkeypatch.setenv("EMAIL_PROVIDER", "sendgrid")
        monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
        monkeypatch.setenv("FROM_EMAIL", "test@billops.com")

        service = EmailNotificationService()

        with patch.object(service.email_service, "send_alert_email") as mock_send:
            mock_send.return_value = True

            success = service.send_payment_confirmation(
                recipient_email="client@example.com",
                recipient_name="Acme Corp",
                invoice_number="INV-001",
                payment_amount_cents=150000,
            )

            assert success is True

    def test_send_overdue_alert(self, monkeypatch):
        """Test sending overdue invoice alert."""
        monkeypatch.setenv("EMAIL_PROVIDER", "sendgrid")
        monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
        monkeypatch.setenv("FROM_EMAIL", "test@billops.com")

        service = EmailNotificationService()

        with patch.object(service.email_service, "send_alert_email") as mock_send:
            mock_send.return_value = True

            success = service.send_invoice_overdue_alert(
                recipient_email="client@example.com",
                recipient_name="Late Payer",
                invoice_number="INV-001",
                invoice_total_cents=150000,
                days_overdue=15,
            )

            assert success is True


class TestSlackMessageFormatting:
    """Tests for Slack message formatting."""

    def test_slack_message_builder(self):
        """Test SlackMessageBuilder."""
        builder = SlackMessageBuilder()
        message = (
            builder.add_header("Test Header")
            .add_section("Test section text")
            .add_divider()
            .build("Test")
        )

        assert "blocks" in message
        assert len(message["blocks"]) >= 3

    def test_format_invoice_message(self):
        """Test formatting invoice message for Slack."""
        message = format_invoice_message(
            invoice_number="INV-2024-001",
            client_name="Acme Corp",
            amount=1500.00,
            status="sent",
        )

        assert "blocks" in message
        assert "text" in message
        assert "INV-2024-001" in message["text"]

    def test_format_payment_message(self):
        """Test formatting payment message for Slack."""
        message = format_payment_message(
            invoice_number="INV-2024-001",
            client_name="Acme Corp",
            amount=1500.00,
        )

        assert "blocks" in message
        # Should contain payment information
        assert len(message["blocks"]) > 0

    def test_format_daily_summary_message(self):
        """Test formatting daily summary message for Slack."""
        message = format_daily_summary_message(
            user_name="John Doe",
            total_hours=8.5,
            entry_count=5,
        )

        assert "blocks" in message
        # Should contain summary information
        assert len(message["blocks"]) > 0

    def test_message_color_coding(self):
        """Test message color coding for different statuses."""
        from app.services.slack_message_formatter import MessageColor

        assert MessageColor.SUCCESS == "#36a64f"
        assert MessageColor.WARNING == "#ff9900"
        assert MessageColor.ERROR == "#ff0000"
        assert MessageColor.INFO == "#0099ff"


class TestSlackNotificationService:
    """Tests for Slack notification service."""

    def test_send_invoice_notification_to_slack(self, monkeypatch):
        """Test sending invoice notification to Slack."""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")

        service = SlackNotificationService(bot_token="xoxb-test-token")

        with patch.object(service.client, "chat_postMessage") as mock_send:
            mock_send.return_value = {"ok": True}

            success = service.send_invoice_notification(
                channel="C123456",
                invoice_number="INV-001",
                client_name="Acme Corp",
                amount_cents=150000,
                status="sent",
            )

            assert success is True
            mock_send.assert_called_once()

    def test_send_payment_notification_to_slack(self, monkeypatch):
        """Test sending payment notification to Slack."""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")

        service = SlackNotificationService(bot_token="xoxb-test-token")

        with patch.object(service.client, "chat_postMessage") as mock_send:
            mock_send.return_value = {"ok": True}

            success = service.send_payment_notification(
                channel="C123456",
                invoice_number="INV-001",
                client_name="Acme Corp",
                amount_cents=150000,
            )

            assert success is True

    def test_slack_notification_without_token(self):
        """Test Slack notification fails gracefully without token."""
        service = SlackNotificationService(bot_token=None)

        success = service.send_invoice_notification(
            channel="C123456",
            invoice_number="INV-001",
            client_name="Acme Corp",
            amount_cents=150000,
            status="sent",
        )

        assert success is False

    def test_send_overdue_invoice_to_slack(self, monkeypatch):
        """Test sending overdue invoice alert to Slack."""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")

        service = SlackNotificationService(bot_token="xoxb-test-token")

        with patch.object(service.client, "chat_postMessage") as mock_send:
            mock_send.return_value = {"ok": True}

            success = service.send_overdue_invoice_alert(
                channel="C123456",
                invoice_number="INV-001",
                client_name="Late Payer",
                amount=1500.00,
                days_overdue=15,
            )

            assert success is True


class TestNotificationIntegration:
    """Integration tests for email and Slack notifications."""

    def test_invoice_notification_workflow(self, monkeypatch):
        """Test complete invoice notification workflow."""
        monkeypatch.setenv("EMAIL_PROVIDER", "sendgrid")
        monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
        monkeypatch.setenv("FROM_EMAIL", "test@billops.com")
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")

        email_service = EmailNotificationService()
        slack_service = SlackNotificationService(bot_token="xoxb-test-token")

        with patch.object(email_service.email_service, "send_invoice_email") as mock_email, \
             patch.object(slack_service.client, "chat_postMessage") as mock_slack:

            mock_email.return_value = True
            mock_slack.return_value = {"ok": True}

            # Send email
            email_success = email_service.send_invoice_notification(
                recipient_email="client@example.com",
                recipient_name="Acme Corp",
                invoice_number="INV-001",
                invoice_total_cents=150000,
                invoice_html="<h1>Invoice</h1>",
            )

            # Send Slack
            slack_success = slack_service.send_invoice_notification(
                channel="C123456",
                invoice_number="INV-001",
                client_name="Acme Corp",
                amount_cents=150000,
                status="sent",
            )

            assert email_success is True
            assert slack_success is True

    def test_payment_notification_workflow(self, monkeypatch):
        """Test complete payment notification workflow."""
        monkeypatch.setenv("EMAIL_PROVIDER", "sendgrid")
        monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
        monkeypatch.setenv("FROM_EMAIL", "test@billops.com")
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")

        email_service = EmailNotificationService()
        slack_service = SlackNotificationService(bot_token="xoxb-test-token")

        with patch.object(email_service.email_service, "send_alert_email") as mock_email, \
             patch.object(slack_service.client, "chat_postMessage") as mock_slack:

            mock_email.return_value = True
            mock_slack.return_value = {"ok": True}

            email_success = email_service.send_payment_confirmation(
                recipient_email="client@example.com",
                recipient_name="Acme Corp",
                invoice_number="INV-001",
                payment_amount_cents=150000,
            )

            slack_success = slack_service.send_payment_notification(
                channel="C123456",
                invoice_number="INV-001",
                client_name="Acme Corp",
                amount_cents=150000,
            )

            assert email_success is True
            assert slack_success is True
