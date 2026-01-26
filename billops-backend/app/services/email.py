"""Email service with support for SendGrid and AWS SES."""
from __future__ import annotations

import logging
from typing import Any
from abc import ABC, abstractmethod

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class EmailProvider(ABC):
    """Abstract base class for email providers."""

    @abstractmethod
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: str | None = None,
        attachments: dict[str, bytes] | None = None,
    ) -> bool:
        """Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional)
            cc: List of CC email addresses
            bcc: List of BCC email addresses
            reply_to: Reply-to email address
            attachments: Dict of filename -> file bytes

        Returns:
            True if sent successfully, False otherwise
        """
        pass


class SendGridEmailProvider(EmailProvider):
    """SendGrid email provider."""

    def __init__(self):
        self.settings = get_settings()
        if not self.settings.sendgrid_api_key:
            raise ValueError("SendGrid API key not configured")

        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment

            self.sendgrid_client = SendGridAPIClient(self.settings.sendgrid_api_key)
            self.Mail = Mail
            self.Email = Email
            self.To = To
            self.Content = Content
            self.Attachment = Attachment
        except ImportError:
            raise ImportError("sendgrid package is required for SendGrid support")

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: str | None = None,
        attachments: dict[str, bytes] | None = None,
    ) -> bool:
        """Send email via SendGrid."""
        try:
            from sendgrid.helpers.mail import Cc, Bcc, ReplyTo

            mail = self.Mail(
                from_email=self.Email(
                    email=self.settings.from_email,
                    name=self.settings.from_name,
                ),
                to_emails=self.To(to_email),
                subject=subject,
                plain_text_content=text_content,
                html_content=html_content,
            )

            if cc:
                for cc_email in cc:
                    mail.add_cc(Cc(cc_email))

            if bcc:
                for bcc_email in bcc:
                    mail.add_bcc(Bcc(bcc_email))

            if reply_to:
                mail.reply_to = ReplyTo(reply_to)

            if attachments:
                import base64
                for filename, content in attachments.items():
                    mail.add_attachment(
                        file_content=base64.b64encode(content).decode(),
                        file_type="application/pdf",
                        file_name=filename,
                    )

            response = self.sendgrid_client.send(mail)
            success = 200 <= response.status_code < 300

            if success:
                logger.info(f"Email sent successfully to {to_email} via SendGrid")
            else:
                logger.error(
                    f"Failed to send email to {to_email} via SendGrid: "
                    f"Status {response.status_code}"
                )

            return success

        except Exception as e:
            logger.error(f"Error sending email via SendGrid: {e}", exc_info=True)
            return False


class AWSEmailProvider(EmailProvider):
    """AWS SES email provider."""

    def __init__(self):
        self.settings = get_settings()
        try:
            import boto3

            self.ses_client = boto3.client(
                "ses",
                region_name=self.settings.ses_region,
                aws_access_key_id=self.settings.ses_access_key_id,
                aws_secret_access_key=self.settings.ses_secret_access_key,
            )
        except ImportError:
            raise ImportError("boto3 package is required for AWS SES support")

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: str | None = None,
        attachments: dict[str, bytes] | None = None,
    ) -> bool:
        """Send email via AWS SES."""
        try:
            # Build email message
            message = {
                "Subject": {"Data": subject},
                "Body": {
                    "Html": {"Data": html_content},
                },
            }

            # Add plain text if provided
            if text_content:
                message["Body"]["Text"] = {"Data": text_content}

            # Note: AWS SES doesn't support attachments via simple send API
            # For attachments, would need to use raw email format
            if attachments:
                logger.warning("AWS SES: Attachments require raw email format")
                return self._send_raw_email(
                    to_email=to_email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                    cc=cc,
                    bcc=bcc,
                    reply_to=reply_to,
                    attachments=attachments,
                )

            # Build destination
            destination = {"ToAddresses": [to_email]}
            if cc:
                destination["CcAddresses"] = cc
            if bcc:
                destination["BccAddresses"] = bcc

            # Send email
            response = self.ses_client.send_email(
                Source=f"{self.settings.from_name} <{self.settings.from_email}>",
                Destination=destination,
                Message=message,
                ReplyToAddresses=[reply_to] if reply_to else [],
            )

            logger.info(f"Email sent successfully to {to_email} via AWS SES")
            return True

        except Exception as e:
            logger.error(f"Error sending email via AWS SES: {e}", exc_info=True)
            return False

    def _send_raw_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: str | None = None,
        attachments: dict[str, bytes] | None = None,
    ) -> bool:
        """Send email with attachments using raw email format."""
        try:
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.base import MIMEBase
            from email import encoders

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.settings.from_name} <{self.settings.from_email}>"
            msg["To"] = to_email

            if cc:
                msg["Cc"] = ", ".join(cc)
            if reply_to:
                msg["Reply-To"] = reply_to

            # Add text and HTML parts
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Add attachments
            if attachments:
                for filename, content in attachments.items():
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(content)
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=filename,
                    )
                    msg.attach(part)

            # Send raw email
            response = self.ses_client.send_raw_email(
                RawMessage={"Data": msg.as_string()},
                Source=self.settings.from_email,
                Destinations=[to_email] + (cc or []) + (bcc or []),
            )

            logger.info(f"Raw email sent successfully to {to_email} via AWS SES")
            return True

        except Exception as e:
            logger.error(f"Error sending raw email via AWS SES: {e}", exc_info=True)
            return False


class EmailService:
    """Main email service that delegates to configured provider."""

    def __init__(self):
        self.settings = get_settings()
        self.provider = self._initialize_provider()

    def _initialize_provider(self) -> EmailProvider:
        """Initialize the configured email provider."""
        provider_type = self.settings.email_provider.lower()

        if provider_type == "sendgrid":
            try:
                return SendGridEmailProvider()
            except (ImportError, ValueError) as e:
                logger.error(f"Failed to initialize SendGrid: {e}")
                raise

        elif provider_type == "ses":
            try:
                return AWSEmailProvider()
            except (ImportError, ValueError) as e:
                logger.error(f"Failed to initialize AWS SES: {e}")
                raise

        else:
            raise ValueError(f"Unknown email provider: {provider_type}")

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: str | None = None,
        attachments: dict[str, bytes] | None = None,
    ) -> bool:
        """Send an email using the configured provider.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body
            cc: List of CC email addresses
            bcc: List of BCC email addresses
            reply_to: Reply-to email address
            attachments: Dict of filename -> file bytes

        Returns:
            True if sent successfully, False otherwise
        """
        return self.provider.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
            attachments=attachments,
        )

    def send_invoice_email(
        self,
        to_email: str,
        client_name: str,
        invoice_number: str,
        invoice_total: float,
        html_content: str,
        pdf_bytes: bytes | None = None,
        due_date: str | None = None,
    ) -> bool:
        """Send invoice email with standard formatting.

        Args:
            to_email: Recipient email address
            client_name: Client name
            invoice_number: Invoice number
            invoice_total: Invoice total amount
            html_content: HTML email body
            pdf_bytes: PDF invoice bytes (optional)
            due_date: Invoice due date (optional)

        Returns:
            True if sent successfully
        """
        subject = f"Invoice {invoice_number} from BillOps"

        # Create plain text version
        text_content = (
            f"Dear {client_name},\n\n"
            f"Invoice {invoice_number} is ready.\n"
            f"Amount due: ${invoice_total:,.2f}\n"
        )
        if due_date:
            text_content += f"Due date: {due_date}\n"
        text_content += (
            "\nPlease see the attached PDF for details.\n\n"
            "Thank you for your business."
        )

        attachments = None
        if pdf_bytes:
            attachments = {
                f"Invoice_{invoice_number}.pdf": pdf_bytes,
            }

        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            attachments=attachments,
        )

    def send_alert_email(
        self,
        to_email: str,
        alert_title: str,
        alert_message: str,
        alert_type: str = "info",
    ) -> bool:
        """Send alert email with standard formatting.

        Args:
            to_email: Recipient email address
            alert_title: Alert title
            alert_message: Alert message
            alert_type: Alert type (info, warning, error, success)

        Returns:
            True if sent successfully
        """
        # Color coding for alert type
        colors = {
            "success": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545",
            "info": "#17a2b8",
        }
        color = colors.get(alert_type, colors["info"])

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert {{ border: 1px solid {color}; padding: 16px; border-radius: 4px; }}
                .alert-title {{ color: {color}; font-weight: bold; font-size: 18px; margin-bottom: 8px; }}
                .alert-message {{ color: #333; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="alert">
                <div class="alert-title">{alert_title}</div>
                <div class="alert-message">{alert_message}</div>
            </div>
        </body>
        </html>
        """

        text_content = f"{alert_title}\n\n{alert_message}"

        return self.send_email(
            to_email=to_email,
            subject=f"Alert: {alert_title}",
            html_content=html_content,
            text_content=text_content,
        )
