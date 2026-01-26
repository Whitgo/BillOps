# Email Service Guide

## Overview

The Email Service provides a flexible, provider-agnostic interface for sending emails via multiple providers (SendGrid and AWS SES). The service handles invoice delivery, payment confirmations, and system alerts.

## Architecture

### Multi-Provider Support

The email service uses an abstract provider pattern:

```python
EmailProvider (abstract)
├── SendGridEmailProvider
└── AWSEmailProvider
```

### Provider Selection

Select the email provider via environment variables:

```bash
# SendGrid
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your_sendgrid_api_key
FROM_EMAIL=noreply@billops.com
FROM_NAME=BillOps

# OR AWS SES
EMAIL_PROVIDER=ses
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
FROM_EMAIL=noreply@billops.com
FROM_NAME=BillOps
```

## Email Service API

### EmailService Class

Main service class for sending emails.

```python
from app.services.email import EmailService

email_service = EmailService()
```

#### Methods

**send_email()**
```python
def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str = None,
    cc: list[str] = None,
    bcc: list[str] = None,
    reply_to: str = None,
    attachments: list[dict] = None,
) -> bool:
    """
    Send a generic email.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML email body
        text_content: Plain text fallback (optional)
        cc: CC recipients list (optional)
        bcc: BCC recipients list (optional)
        reply_to: Reply-to email address (optional)
        attachments: List of attachment dicts with 'filename' and 'content' (optional)
    
    Returns:
        bool: True if successful, False otherwise
    """
```

**send_invoice_email()**
```python
def send_invoice_email(
    to_email: str,
    client_name: str,
    invoice_number: str,
    invoice_total: float,
    html_content: str,
    pdf_bytes: bytes = None,
) -> bool:
    """Send an invoice email with optional PDF attachment."""
```

**send_alert_email()**
```python
def send_alert_email(
    to_email: str,
    alert_title: str,
    alert_message: str,
    alert_type: str = "info",  # info, warning, error
) -> bool:
    """Send an alert/notification email."""
```

## Email Notification Service

### EmailNotificationService Class

High-level service for application-specific email notifications.

```python
from app.services.notifications.email import EmailNotificationService

email_notifier = EmailNotificationService()
```

#### Methods

**send_invoice_notification()**
```python
def send_invoice_notification(
    recipient_email: str,
    recipient_name: str,
    invoice_number: str,
    invoice_total_cents: int,
    invoice_html: str,
    pdf_bytes: bytes = None,
) -> bool:
    """Send invoice to client."""
```

**send_payment_confirmation()**
```python
def send_payment_confirmation(
    recipient_email: str,
    recipient_name: str,
    invoice_number: str,
    payment_amount_cents: int,
    payment_date: str = None,
) -> bool:
    """Send payment confirmation email."""
```

**send_invoice_overdue_alert()**
```python
def send_invoice_overdue_alert(
    recipient_email: str,
    recipient_name: str,
    invoice_number: str,
    invoice_total_cents: int,
    days_overdue: int,
) -> bool:
    """Send overdue invoice reminder."""
```

**send_time_entry_reminder()**
```python
def send_time_entry_reminder(
    recipient_email: str,
    recipient_name: str,
    project_name: str,
    reminder_type: str = "daily",
) -> bool:
    """Send time entry reminder (daily, weekly, etc)."""
```

## Usage Examples

### SendGrid Provider

```python
import os
os.environ['EMAIL_PROVIDER'] = 'sendgrid'
os.environ['SENDGRID_API_KEY'] = 'SG.xxx'

from app.services.email import EmailService

service = EmailService()
service.send_email(
    to_email="user@example.com",
    subject="Invoice #INV-001",
    html_content="<h1>Invoice</h1><p>Amount: $1,500</p>",
    attachments=[
        {
            'filename': 'invoice.pdf',
            'content': pdf_bytes,
            'mime_type': 'application/pdf'
        }
    ]
)
```

### AWS SES Provider

```python
import os
os.environ['EMAIL_PROVIDER'] = 'ses'
os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAIOSFODNN7EXAMPLE'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'xxxxx'
os.environ['AWS_REGION'] = 'us-east-1'

from app.services.email import EmailService

service = EmailService()
service.send_email(
    to_email="user@example.com",
    subject="Invoice #INV-001",
    html_content="<h1>Invoice</h1><p>Amount: $1,500</p>",
    cc=["manager@example.com"],
    reply_to="billing@example.com"
)
```

### Using EmailNotificationService

```python
from app.services.notifications.email import EmailNotificationService

notifier = EmailNotificationService()

# Send invoice to client
notifier.send_invoice_notification(
    recipient_email="client@example.com",
    recipient_name="Acme Corp",
    invoice_number="INV-001",
    invoice_total_cents=150000,  # $1,500.00
    invoice_html="<h1>Invoice</h1>",
    pdf_bytes=pdf_content
)

# Send payment confirmation
notifier.send_payment_confirmation(
    recipient_email="client@example.com",
    recipient_name="Acme Corp",
    invoice_number="INV-001",
    payment_amount_cents=150000
)

# Send overdue reminder
notifier.send_invoice_overdue_alert(
    recipient_email="client@example.com",
    recipient_name="Acme Corp",
    invoice_number="INV-001",
    invoice_total_cents=150000,
    days_overdue=5
)
```

## Email Templates

### Invoice Email Template

The invoice email includes:
- Invoice header with company branding
- Invoice number and date
- Client information
- Itemized line items
- Total amount and due date
- Payment instructions
- Company contact information

### Payment Confirmation Template

The payment email includes:
- Payment confirmation header
- Payment amount and date
- Reference invoice number
- Thank you message
- Company footer

### Overdue Alert Template

The overdue email includes:
- Alert header with warning
- Invoice number and amount
- Number of days overdue
- Payment instructions
- Contact information for questions

## Error Handling

All email methods return a boolean:
- `True`: Email sent successfully
- `False`: Email sending failed

Detailed error information is logged via Python's logging module:

```python
import logging

logger = logging.getLogger(__name__)
# Check application logs for email service errors
```

## Celery Integration

Email sending can be queued as background tasks:

```python
from app.services.tasks.notifications import send_invoice_email

# Queue task
send_invoice_email.delay(
    invoice_id="uuid-string",
    recipient_email="user@example.com",
    recipient_name="John Doe"
)
```

See [NOTIFICATIONS_QUICK_START.md](NOTIFICATIONS_QUICK_START.md) for Celery task documentation.

## Testing

Unit tests available in `tests/integration/test_email_slack_notifications.py`:

```bash
# Run email service tests
pytest tests/integration/test_email_slack_notifications.py::TestEmailService -v

# Run email notification service tests
pytest tests/integration/test_email_slack_notifications.py::TestEmailNotificationService -v
```

## Troubleshooting

### SendGrid Issues

**Error: "Invalid API key"**
- Verify SENDGRID_API_KEY is correct
- Check API key permissions include Mail Send

**Error: "Invalid sender"**
- Verify FROM_EMAIL is a verified sender in SendGrid
- Check domain authentication for custom domains

### AWS SES Issues

**Error: "MessageRejected"**
- Verify AWS credentials are correct
- Check SES is enabled for your AWS region
- Verify sender email is verified in SES (sandbox mode)
- In production, request SES sending limit increase

**Error: "We cannot process this request"**
- Email may be in SES spam/complaint feedback loop
- Check SES dashboard for bounce/complaint metrics

## Production Deployment

1. **Set production credentials**
   ```bash
   export EMAIL_PROVIDER=sendgrid  # or 'ses'
   export SENDGRID_API_KEY="your-production-key"  # or SES credentials
   ```

2. **Configure verified senders**
   - SendGrid: Verify domain or individual email
   - SES: Verify sender email (or domain in production mode)

3. **Monitor delivery**
   - Check SendGrid/SES dashboards for bounce/complaint rates
   - Monitor application logs for email errors
   - Set up email delivery webhooks if needed

4. **Rate limiting**
   - Be aware of SendGrid/SES rate limits
   - Consider rate limiting in application code for high-volume scenarios

## Cost Considerations

- **SendGrid**: Free tier 100 emails/day, paid plans from $19.95/month
- **AWS SES**: $0.10 per 1,000 emails, included in AWS free tier for 62,000 emails/month

Choose provider based on volume and cost requirements.
