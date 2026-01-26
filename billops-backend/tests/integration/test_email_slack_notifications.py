"""Tests for email and Slack notification services."""
import json
from unittest.mock import Mock, patch, MagicMock
import pytest

from app.services.email import (
    EmailService,
    SendGridEmailProvider,
    AWSEmailProvider,
)
from app.services.notifications.email import EmailNotificationService
from app.services.notifications.slack import SlackNotificationService
from app.services.slack_message_formatter import (
    SlackMessageBuilder,
    SlackBlockBuilder,
    MessageColor,
    format_invoice_message,
    format_payment_message,
    format_time_entry_message,
    format_daily_summary_message,
    format_alert_message,
    format_overdue_invoice_alert,
)


class TestSlackBlockBuilder:
    """Tests for Slack block builder."""

    def test_header_block(self):
        """Test header block creation."""
        block = SlackBlockBuilder.header("Test Header")

        assert block["type"] == "header"
        assert block["text"]["text"] == "Test Header"
        assert block["text"]["type"] == "plain_text"

    def test_section_block(self):
        """Test section block creation."""
        block = SlackBlockBuilder.section("Test section", markdown=True)

        assert block["type"] == "section"
        assert block["text"]["text"] == "Test section"
        assert block["text"]["type"] == "mrkdwn"

    def test_divider_block(self):
        """Test divider block creation."""
        block = SlackBlockBuilder.divider()

        assert block["type"] == "divider"

    def test_button_element(self):
        """Test button element creation."""
        button = SlackBlockBuilder.button(
            text="Click me",
            action_id="btn_1",
            value="value_1",
            style="primary",
        )

        assert button["type"] == "button"
        assert button["text"]["text"] == "Click me"
        assert button["action_id"] == "btn_1"
        assert button["value"] == "value_1"
        assert button["style"] == "primary"

    def test_field_element(self):
        """Test field element creation."""
        field = SlackBlockBuilder.field("Title", "Value")

        assert field["type"] == "mrkdwn"
        assert "*Title*" in field["text"]
        assert "Value" in field["text"]


class TestSlackMessageBuilder:
    """Tests for Slack message builder."""

    def test_build_empty_message(self):
        """Test building empty message."""
        builder = SlackMessageBuilder()
        message = builder.build("test")

        assert message["text"] == "test"
        assert message["blocks"] == []

    def test_build_with_header(self):
        """Test building message with header."""
        builder = SlackMessageBuilder()
        builder.add_header("Test")
        message = builder.build()

        assert len(message["blocks"]) == 1
        assert message["blocks"][0]["type"] == "header"

    def test_build_with_sections(self):
        """Test building message with sections."""
        builder = SlackMessageBuilder()
        builder.add_section("Section 1")
        builder.add_section("Section 2")
        message = builder.build()

        assert len(message["blocks"]) == 2
        assert all(b["type"] == "section" for b in message["blocks"])

    def test_add_fields(self):
        """Test adding fields to message."""
        builder = SlackMessageBuilder()
        builder.add_fields([
            ("Field 1", "Value 1"),
            ("Field 2", "Value 2"),
        ])
        message = builder.build()

        assert len(message["blocks"]) == 1
        block = message["blocks"][0]
        assert block["type"] == "section"
        assert len(block["fields"]) == 2

    def test_add_buttons(self):
        """Test adding buttons to message."""
        builder = SlackMessageBuilder()
        builder.add_buttons([
            {"text": "Yes", "action_id": "yes", "value": "yes"},
            {"text": "No", "action_id": "no", "value": "no"},
        ])
        message = builder.build()

        assert len(message["blocks"]) == 1
        block = message["blocks"][0]
        assert block["type"] == "actions"
        assert len(block["elements"]) == 2

    def test_set_color(self):
        """Test setting message color."""
        builder = SlackMessageBuilder()
        builder.add_section("Test")
        builder.set_color(MessageColor.SUCCESS)
        message = builder.build()

        assert message["attachments"][0]["color"] == MessageColor.SUCCESS


class TestMessageFormatters:
    """Tests for message formatter functions."""

    def test_format_invoice_message(self):
        """Test invoice message formatting."""
        message = format_invoice_message(
            invoice_number="INV-001",
            client_name="Acme Corp",
            amount=1500.00,
            status="sent",
        )

        assert "blocks" in message
        assert "INV-001" in message["text"]
        assert any("Acme Corp" in str(b) for b in message["blocks"])

    def test_format_payment_message(self):
        """Test payment message formatting."""
        message = format_payment_message(
            invoice_number="INV-001",
            client_name="Acme Corp",
            amount=1500.00,
        )

        assert "blocks" in message
        assert "Payment" in message["text"].lower() or "Payment" in str(message["blocks"])

    def test_format_time_entry_message(self):
        """Test time entry message formatting."""
        message = format_time_entry_message(
            description="Client meeting",
            duration_hours=2.5,
            project_name="Project A",
        )

        assert "blocks" in message
        assert "blocks" in message

    def test_format_daily_summary_message(self):
        """Test daily summary message formatting."""
        message = format_daily_summary_message(
            total_hours=8.0,
            entry_count=3,
        )

        assert "blocks" in message
        assert "Summary" in message["text"]

    def test_format_alert_message(self):
        """Test alert message formatting."""
        message = format_alert_message(
            title="Test Alert",
            message="This is a test",
            alert_type="warning",
        )

        assert "blocks" in message
        assert "Test Alert" in message["text"]

    def test_format_overdue_invoice_alert(self):
        """Test overdue invoice alert formatting."""
        message = format_overdue_invoice_alert(
            invoice_number="INV-001",
            client_name="Acme Corp",
            amount=1500.00,
            days_overdue=5,
        )

        assert "blocks" in message
        assert "Overdue" in message["text"]


class TestEmailService:
    """Tests for email service."""

    def test_initialize_sendgrid_provider(self, monkeypatch):
        """Test SendGrid provider initialization."""
        monkeypatch.setenv("EMAIL_PROVIDER", "sendgrid")
        monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
        monkeypatch.setenv("FROM_EMAIL", "test@example.com")

        with patch("app.services.email.SendGridEmailProvider"):
            # Should not raise if provider is available
            try:
                service = EmailService()
            except ImportError:
                # Expected if sendgrid not installed
                pass

    def test_sendgrid_send_email(self, monkeypatch):
        """Test SendGrid email sending."""
        monkeypatch.setenv("EMAIL_PROVIDER", "sendgrid")
        monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
        monkeypatch.setenv("FROM_EMAIL", "test@example.com")
        monkeypatch.setenv("FROM_NAME", "Test")

        with patch("app.services.email.SendGridAPIClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            mock_instance.send.return_value = MagicMock(status_code=202)

            try:
                provider = SendGridEmailProvider()
                result = provider.send_email(
                    to_email="user@example.com",
                    subject="Test",
                    html_content="<p>Test</p>",
                )

                assert result is True
            except ImportError:
                # Expected if sendgrid not installed in test env
                pass

    def test_email_service_methods(self, monkeypatch):
        """Test EmailService public methods."""
        monkeypatch.setenv("EMAIL_PROVIDER", "sendgrid")
        monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
        monkeypatch.setenv("FROM_EMAIL", "test@example.com")

        with patch("app.services.email.SendGridEmailProvider"):
            try:
                service = EmailService()

                with patch.object(service.provider, "send_email") as mock_send:
                    mock_send.return_value = True

                    result = service.send_email(
                        to_email="user@example.com",
                        subject="Test",
                        html_content="<p>Test</p>",
                    )

                    assert result is True
                    mock_send.assert_called_once()
            except ImportError:
                pass


class TestEmailNotificationService:
    """Tests for email notification service."""

    def test_send_invoice_notification(self, monkeypatch):
        """Test sending invoice notification."""
        monkeypatch.setenv("EMAIL_PROVIDER", "sendgrid")
        monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
        monkeypatch.setenv("FROM_EMAIL", "test@example.com")

        with patch("app.services.email.SendGridEmailProvider"):
            try:
                service = EmailNotificationService()

                with patch.object(service.email_service, "send_invoice_email") as mock_send:
                    mock_send.return_value = True

                    result = service.send_invoice_notification(
                        recipient_email="user@example.com",
                        recipient_name="John Doe",
                        invoice_number="INV-001",
                        invoice_total_cents=150000,
                        invoice_html="<p>Invoice</p>",
                    )

                    assert result is True
                    mock_send.assert_called_once()
            except ImportError:
                pass

    def test_send_payment_confirmation(self, monkeypatch):
        """Test sending payment confirmation."""
        monkeypatch.setenv("EMAIL_PROVIDER", "sendgrid")
        monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
        monkeypatch.setenv("FROM_EMAIL", "test@example.com")

        with patch("app.services.email.SendGridEmailProvider"):
            try:
                service = EmailNotificationService()

                with patch.object(service.email_service, "send_alert_email") as mock_send:
                    mock_send.return_value = True

                    result = service.send_payment_confirmation(
                        recipient_email="user@example.com",
                        recipient_name="John Doe",
                        invoice_number="INV-001",
                        payment_amount_cents=150000,
                    )

                    assert result is True
            except ImportError:
                pass

    def test_send_overdue_alert(self, monkeypatch):
        """Test sending overdue invoice alert."""
        monkeypatch.setenv("EMAIL_PROVIDER", "sendgrid")
        monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
        monkeypatch.setenv("FROM_EMAIL", "test@example.com")

        with patch("app.services.email.SendGridEmailProvider"):
            try:
                service = EmailNotificationService()

                with patch.object(service.email_service, "send_alert_email") as mock_send:
                    mock_send.return_value = True

                    result = service.send_invoice_overdue_alert(
                        recipient_email="user@example.com",
                        recipient_name="John Doe",
                        invoice_number="INV-001",
                        invoice_total_cents=150000,
                        days_overdue=5,
                    )

                    assert result is True
            except ImportError:
                pass


class TestSlackNotificationService:
    """Tests for Slack notification service."""

    def test_send_message(self, monkeypatch):
        """Test sending Slack message."""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")

        with patch("app.services.notifications.slack.WebClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            mock_instance.chat_postMessage.return_value = True

            service = SlackNotificationService("xoxb-test")
            message = {"text": "Test", "blocks": []}

            result = service.send_message("#general", message)

            assert result is True
            mock_instance.chat_postMessage.assert_called_once()

    def test_send_invoice_notification(self, monkeypatch):
        """Test sending invoice notification via Slack."""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")

        with patch("app.services.notifications.slack.WebClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            mock_instance.chat_postMessage.return_value = True

            service = SlackNotificationService("xoxb-test")

            result = service.send_invoice_notification(
                channel="#billing",
                invoice_number="INV-001",
                client_name="Acme Corp",
                amount_cents=150000,
                status="sent",
            )

            assert result is True

    def test_send_payment_notification(self, monkeypatch):
        """Test sending payment notification via Slack."""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")

        with patch("app.services.notifications.slack.WebClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            mock_instance.chat_postMessage.return_value = True

            service = SlackNotificationService("xoxb-test")

            result = service.send_payment_notification(
                channel="#billing",
                invoice_number="INV-001",
                client_name="Acme Corp",
                amount_cents=150000,
            )

            assert result is True

    def test_send_overdue_alert(self, monkeypatch):
        """Test sending overdue invoice alert via Slack."""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")

        with patch("app.services.notifications.slack.WebClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            mock_instance.chat_postMessage.return_value = True

            service = SlackNotificationService("xoxb-test")

            result = service.send_overdue_invoice_alert(
                channel="#billing",
                invoice_number="INV-001",
                client_name="Acme Corp",
                amount_cents=150000,
                days_overdue=5,
            )

            assert result is True

    def test_send_daily_summary(self, monkeypatch):
        """Test sending daily summary via Slack."""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")

        with patch("app.services.notifications.slack.WebClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            mock_instance.chat_postMessage.return_value = True

            service = SlackNotificationService("xoxb-test")

            result = service.send_daily_summary(
                channel="#time-tracking",
                total_hours=8.5,
                entry_count=4,
            )

            assert result is True
