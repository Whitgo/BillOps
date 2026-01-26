# Notifications Quick Start

Complete guide to sending emails and Slack notifications in BillOps.

## 5-Minute Setup

### Email Service

1. **Choose a provider**

   **Option A: SendGrid**
   ```bash
   # Get free API key: sendgrid.com/free
   export EMAIL_PROVIDER=sendgrid
   export SENDGRID_API_KEY=SG.xxx
   export FROM_EMAIL=noreply@billops.com
   export FROM_NAME="BillOps"
   ```

   **Option B: AWS SES**
   ```bash
   export EMAIL_PROVIDER=ses
   export AWS_ACCESS_KEY_ID=AKIA...
   export AWS_SECRET_ACCESS_KEY=xxx
   export AWS_REGION=us-east-1
   export FROM_EMAIL=noreply@billops.com
   export FROM_NAME="BillOps"
   ```

2. **Import and use**
   ```python
   from app.services.notifications.email import EmailNotificationService
   
   email = EmailNotificationService()
   email.send_invoice_notification(
       recipient_email="user@example.com",
       recipient_name="John Doe",
       invoice_number="INV-001",
       invoice_total_cents=150000,
       invoice_html="<h1>Invoice</h1>",
   )
   ```

### Slack Service

1. **Create a Slack app**
   - Go to api.slack.com/apps → Create New App
   - Name: "BillOps"
   - Add `chat:write` scope
   - Install to workspace
   - Copy Bot User OAuth Token

2. **Set token**
   ```bash
   export SLACK_BOT_TOKEN=xoxb-your-token
   ```

3. **Send messages**
   ```python
   from app.services.notifications.slack import SlackNotificationService
   
   slack = SlackNotificationService()
   slack.send_invoice_notification(
       channel="#billing",
       invoice_number="INV-001",
       client_name="Acme Corp",
       amount_cents=150000,
       status="sent"
   )
   ```

## Common Tasks

### Send Invoice Email

```python
from app.services.notifications.email import EmailNotificationService

email = EmailNotificationService()
success = email.send_invoice_notification(
    recipient_email="client@example.com",
    recipient_name="Acme Corp",
    invoice_number="INV-001",
    invoice_total_cents=150000,
    invoice_html="<h1>Invoice #INV-001</h1><p>Amount: $1,500</p>",
    pdf_bytes=pdf_content  # Optional
)
```

### Send Invoice to Slack

```python
from app.services.notifications.slack import SlackNotificationService

slack = SlackNotificationService()
success = slack.send_invoice_notification(
    channel="#billing",
    invoice_number="INV-001",
    client_name="Acme Corp",
    amount_cents=150000,
    status="sent",
    due_date="2024-02-15"
)
```

### Send Payment Confirmation

```python
# Email
email.send_payment_confirmation(
    recipient_email="client@example.com",
    recipient_name="Acme Corp",
    invoice_number="INV-001",
    payment_amount_cents=150000
)

# Slack
slack.send_payment_notification(
    channel="#billing",
    invoice_number="INV-001",
    client_name="Acme Corp",
    amount_cents=150000
)
```

### Send Overdue Alert

```python
# Email
email.send_invoice_overdue_alert(
    recipient_email="client@example.com",
    recipient_name="Acme Corp",
    invoice_number="INV-001",
    invoice_total_cents=150000,
    days_overdue=5
)

# Slack
slack.send_overdue_invoice_alert(
    channel="#alerts",
    invoice_number="INV-001",
    client_name="Acme Corp",
    amount_cents=150000,
    days_overdue=5
)
```

### Send Time Entry Notification

```python
slack.send_time_entry_notification(
    channel="#time-tracking",
    description="Client meeting",
    duration_hours=2.5,
    project_name="Project A",
    entry_date="2024-01-15"
)
```

### Send Daily Summary

```python
slack.send_daily_summary(
    channel="#time-tracking",
    total_hours=8.5,
    entry_count=4,
    summary_date="2024-01-15"
)
```

### Custom Email

```python
from app.services.email import EmailService

email_svc = EmailService()
success = email_svc.send_email(
    to_email="user@example.com",
    subject="Custom Email",
    html_content="<p>Custom message</p>",
    text_content="Custom message",
    cc=["cc@example.com"],
    reply_to="support@example.com"
)
```

### Custom Slack Message

```python
from app.services.slack_message_formatter import SlackMessageBuilder, MessageColor

message = (
    SlackMessageBuilder()
    .add_header("Invoice Alert")
    .add_section("*Invoice #INV-001* has been sent", markdown=True)
    .add_fields([
        ("Amount", "$1,500.00"),
        ("Due Date", "2024-02-15"),
    ])
    .add_buttons([
        {
            "text": "View",
            "action_id": "view",
            "value": "INV-001",
            "style": "primary"
        }
    ])
    .set_color(MessageColor.SUCCESS)
    .build()
)

slack.send_message("#billing", message)
```

## Async with Celery

Queue notifications to run asynchronously:

```python
from app.services.tasks.notifications import (
    send_invoice_email,
    send_invoice_slack,
    send_payment_email,
    send_payment_slack,
    send_overdue_invoice_alert,
)

# Queue invoice email (with retries)
send_invoice_email.delay(
    invoice_id="uuid-string",
    recipient_email="user@example.com",
    recipient_name="John Doe"
)

# Queue Slack notification
send_invoice_slack.delay(
    invoice_id="uuid-string",
    channel="#billing"
)

# Queue payment email
send_payment_email.delay(
    invoice_id="uuid-string",
    recipient_email="user@example.com",
    recipient_name="John Doe"
)

# Queue payment Slack notification
send_payment_slack.delay(
    invoice_id="uuid-string",
    channel="#billing"
)

# Queue overdue alert (sends via both email and Slack)
send_overdue_invoice_alert.delay(
    invoice_id="uuid-string",
    recipient_email="user@example.com",
    recipient_name="John Doe",
    slack_channel="#alerts"
)
```

## API Endpoints

POST endpoints to trigger notifications:

```bash
# Send invoice via email
curl -X POST http://localhost:8000/api/v1/notifications/send-invoice-email \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": "uuid",
    "recipient_email": "user@example.com"
  }'

# Send invoice to Slack
curl -X POST http://localhost:8000/api/v1/notifications/send-invoice-slack \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": "uuid",
    "channel": "#billing"
  }'

# Send payment confirmation
curl -X POST http://localhost:8000/api/v1/notifications/send-payment-email \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": "uuid",
    "recipient_email": "user@example.com",
    "payment_amount_cents": 150000
  }'

# Send payment to Slack
curl -X POST http://localhost:8000/api/v1/notifications/send-payment-slack \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": "uuid",
    "channel": "#billing",
    "payment_amount_cents": 150000
  }'

# Send alert
curl -X POST http://localhost:8000/api/v1/notifications/send-alert-email \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_email": "user@example.com",
    "alert_title": "High Overdue Count",
    "alert_message": "5 invoices are now overdue",
    "alert_type": "warning"
  }'

# Send alert to Slack
curl -X POST http://localhost:8000/api/v1/notifications/send-alert-slack \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "#alerts",
    "alert_title": "High Overdue Count",
    "alert_message": "5 invoices are now overdue",
    "alert_type": "warning"
  }'
```

## Environment Configuration

Create `.env` file in project root:

```bash
# Email Provider (sendgrid or ses)
EMAIL_PROVIDER=sendgrid

# SendGrid Configuration
SENDGRID_API_KEY=SG.xxx

# AWS SES Configuration
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=xxx
AWS_REGION=us-east-1

# Email From
FROM_EMAIL=noreply@billops.com
FROM_NAME=BillOps

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-xxx
SLACK_DEFAULT_CHANNEL=#billing
SLACK_ALERTS_CHANNEL=#alerts

# Celery (for async tasks)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Testing

Run tests:

```bash
# All notification tests
pytest tests/integration/test_email_slack_notifications.py -v

# Email tests only
pytest tests/integration/test_email_slack_notifications.py::TestEmailService -v
pytest tests/integration/test_email_slack_notifications.py::TestEmailNotificationService -v

# Slack tests only
pytest tests/integration/test_email_slack_notifications.py::TestSlackMessageBuilder -v
pytest tests/integration/test_email_slack_notifications.py::TestSlackNotificationService -v

# Message formatter tests
pytest tests/integration/test_email_slack_notifications.py::TestMessageFormatters -v
```

## Troubleshooting

### Email not sending?

1. Check provider configuration:
   ```python
   import os
   print(f"Provider: {os.getenv('EMAIL_PROVIDER')}")
   print(f"From: {os.getenv('FROM_EMAIL')}")
   ```

2. Check logs:
   ```bash
   tail -f logs/app.log | grep -i email
   ```

3. Verify API credentials
   - SendGrid: Check key is not revoked
   - SES: Verify sender email, check bounce rate

### Slack not sending?

1. Check token:
   ```python
   import os
   token = os.getenv('SLACK_BOT_TOKEN')
   print(f"Token starts with: {token[:10]}...")
   ```

2. Verify bot permissions
   - Add `chat:write` scope
   - Invite bot to channel: `/invite @BillOps`

3. Check logs:
   ```bash
   tail -f logs/app.log | grep -i slack
   ```

## More Documentation

- [Email Service Guide](EMAIL_SERVICE_GUIDE.md) - Detailed email service documentation
- [Slack Notification Guide](SLACK_NOTIFICATION_GUIDE.md) - Detailed Slack documentation
- [Celery Integration](INTEGRATION_TESTS.md) - Background task integration
- [API Routes](API_ROUTES.md) - All API endpoints
