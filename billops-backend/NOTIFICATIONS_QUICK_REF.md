# Notifications System - Quick Reference

## Quick Start

### 1. Configure Email Provider

Set environment variables:

```bash
# SendGrid
export EMAIL_PROVIDER=sendgrid
export SENDGRID_API_KEY=sg_your_api_key_here

# OR AWS SES
export EMAIL_PROVIDER=ses
export SES_ACCESS_KEY_ID=AKIA...
export SES_SECRET_ACCESS_KEY=...
export SES_REGION=us-east-1

# Common settings
export FROM_EMAIL=noreply@billops.com
export FROM_NAME=BillOps
```

### 2. Configure Slack (Optional)

```bash
export SLACK_BOT_TOKEN=xoxb-your-token-here
export SLACK_SIGNING_SECRET=your-signing-secret
```

### 3. Test Configuration

```bash
# Test email
curl -X POST http://localhost:8000/api/v1/notifications/test/email \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "recipient_email=test@example.com"

# Test Slack
curl -X POST http://localhost:8000/api/v1/notifications/test/slack \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "channel=C123456"

# Check config status
curl http://localhost:8000/api/v1/notifications/config/status
```

## Common Tasks

### Send Invoice Email

```python
from app.services.notifications.email import EmailNotificationService

service = EmailNotificationService()
success = service.send_invoice_notification(
    recipient_email="client@example.com",
    recipient_name="Acme Corp",
    invoice_number="INV-001",
    invoice_total_cents=150000,  # $1,500.00
    invoice_html=html_content,
    due_date=datetime(2024, 2, 15),
)
```

### Send Slack Notification

```python
from app.services.notifications.slack import SlackNotificationService
from app.config.settings import Settings

settings = Settings()
service = SlackNotificationService(bot_token=settings.slack_bot_token)

success = service.send_invoice_notification(
    channel="C123456",
    invoice_number="INV-001",
    client_name="Acme Corp",
    amount_cents=150000,
    status="sent",
)
```

### Generate Email from Template

```python
from app.services.email_templates import EmailTemplates

# Invoice template
templates = EmailTemplates.invoice_template(
    client_name="Acme Corp",
    invoice_number="INV-001",
    invoice_date=datetime(2024, 1, 15),
    due_date=datetime(2024, 2, 15),
    total_amount=1500.00,
    items=[
        {"description": "Development", "quantity": 40, "rate": 150},
    ],
)
html = templates["html"]
text = templates["text"]

# Payment template
templates = EmailTemplates.payment_confirmation_template(
    client_name="Acme Corp",
    invoice_number="INV-001",
    payment_amount=1500.00,
    payment_date=datetime.now(),
)

# Overdue template
templates = EmailTemplates.overdue_invoice_template(
    client_name="Late Payer",
    invoice_number="INV-001",
    amount_due=1500.00,
    days_overdue=15,
    due_date=datetime(2024, 1, 1),
)

# Time summary template
templates = EmailTemplates.time_entry_summary_template(
    user_name="John Doe",
    summary_date=datetime.now(),
    total_hours=8.5,
    entry_count=5,
)
```

### Queue Async Email Task

```python
from app.services.tasks.notifications import send_invoice_email

task = send_invoice_email.delay(
    invoice_id="550e8400-e29b-41d4-a716-446655440000",
    recipient_email="client@example.com",
    recipient_name="Acme Corp",
)

# Check status later
from app.celery_app import celery_app
result = celery_app.AsyncResult(task.id)
print(result.state)  # PENDING, STARTED, SUCCESS, FAILURE
```

### Format Slack Message

```python
from app.services.slack_message_formatter import (
    format_invoice_message,
    format_payment_message,
    format_daily_summary_message,
    SlackMessageBuilder,
    MessageColor,
)

# Preset message
message = format_invoice_message(
    invoice_number="INV-001",
    client_name="Acme Corp",
    amount=1500.00,
    status="sent",
)

# Custom message with builder
builder = SlackMessageBuilder()
message = (
    builder.add_header("Invoice #INV-001")
    .add_section("*Client:* Acme Corp\n*Amount:* $1,500.00")
    .add_divider()
    .add_section("Payment due: Feb 15, 2024")
    .build()
)
```

## API Endpoints

### Email Operations

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/send-invoice-email` | Send invoice via email |
| POST | `/send-payment-email` | Send payment confirmation |
| POST | `/send-alert-email` | Send alert email |
| POST | `/test/email` | Test email configuration |

### Slack Operations

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/send-invoice-slack` | Send invoice to Slack |
| POST | `/send-payment-slack` | Send payment to Slack |
| POST | `/send-alert-slack` | Send alert to Slack |
| POST | `/test/slack` | Test Slack configuration |

### Utility Operations

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/overdue/check` | Check overdue invoices |
| GET | `/status/{task_id}` | Get task status |
| GET | `/config/status` | Get configuration status |
| GET | `/health` | Health check |

## Debugging

### Check if Celery worker is running

```bash
ps aux | grep celery
```

### View active tasks

```bash
celery -A app.celery_app inspect active
```

### Monitor task execution

```bash
celery -A app.celery_app events
```

### View application logs

```bash
tail -f logs/app.log | grep notification
```

### Manually inspect task result

```python
from app.celery_app import celery_app

result = celery_app.AsyncResult('task-id-here')
print(f"State: {result.state}")
print(f"Result: {result.result}")
print(f"Info: {result.info}")
```

### Test email service directly

```python
from app.services.email import EmailService

service = EmailService()
success = service.send_email(
    to_email="test@example.com",
    subject="Test",
    html_content="<h1>Test Email</h1>",
)
print(f"Email sent: {success}")
```

### Verify template rendering

```python
from app.services.email_templates import EmailTemplates
import json

templates = EmailTemplates.invoice_template(
    client_name="Test",
    invoice_number="TEST-001",
    invoice_date=datetime.now(),
    due_date=None,
    total_amount=1000.00,
)

# Print to file for review
with open("test_invoice.html", "w") as f:
    f.write(templates["html"])
print("Check test_invoice.html in your editor")
```

## Troubleshooting

### Email not sending

1. Check environment variables are set
2. Test with `POST /test/email`
3. Verify API key with provider (SendGrid/AWS)
4. Check Celery worker is running
5. Review logs: `tail -f logs/app.log | grep email`

### Slack messages not posting

1. Verify SLACK_BOT_TOKEN is set
2. Verify bot is added to channel
3. Test with `POST /test/slack?channel=C123456`
4. Check permissions: bot needs `chat:write`
5. Review logs: `tail -f logs/app.log | grep slack`

### Task not executing

1. Verify Celery worker: `ps aux | grep celery`
2. Check Redis: `redis-cli ping` (should return PONG)
3. Check queue: `celery -A app.celery_app inspect active_queues`
4. View pending tasks: `celery -A app.celery_app inspect reserved`

### Configuration issues

1. Check status: `GET /config/status`
2. Validate settings loaded: Check `app/config/settings.py`
3. Review environment: `env | grep -i email`
4. Test manually in Python REPL

## Integration with Invoice Workflow

### Option 1: Send on Invoice Creation

```python
# In invoice creation endpoint
from app.services.tasks.notifications import send_invoice_email

invoice = create_invoice(...)

# Queue email notification
send_invoice_email.delay(
    invoice_id=str(invoice.id),
    recipient_email=invoice.client.email,
    recipient_name=invoice.client.name,
)
```

### Option 2: Send on Status Change

```python
# In invoice update endpoint
if invoice.status == "sent":
    send_invoice_email.delay(
        invoice_id=str(invoice.id),
        recipient_email=invoice.client.email,
        recipient_name=invoice.client.name,
    )
elif invoice.status == "paid":
    send_payment_email.delay(
        invoice_id=str(invoice.id),
        recipient_email=invoice.client.email,
        recipient_name=invoice.client.name,
    )
```

### Option 3: Via API Endpoint

```bash
# Send invoice via API
curl -X POST http://localhost:8000/api/v1/notifications/send-invoice-email \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "invoice_id=550e8400-e29b-41d4-a716-446655440000" \
  -d "recipient_email=client@example.com"

# Check task status
curl http://localhost:8000/api/v1/notifications/status/task-id-here
```

## Email Template Variables

All templates support these formatting options:

```python
# Currency support
EmailTemplates.invoice_template(
    total_amount=1500.00,
    currency="USD",  # or "EUR", "GBP", etc.
)

# Date formatting
EmailTemplates.invoice_template(
    invoice_date=datetime(2024, 1, 15),  # Formatted as "Jan 15, 2024"
    due_date=datetime(2024, 2, 15),
)

# Optional line items
EmailTemplates.invoice_template(
    items=[
        {"description": "Development", "quantity": 40, "rate": 150},
        {"description": "Consulting", "quantity": 5, "rate": 200},
    ]
)
```

## Performance Tips

1. **Use async tasks** - Always queue via Celery, don't send synchronously
2. **Batch operations** - Use `check_overdue_invoices()` instead of individual calls
3. **Monitor queue** - Keep Celery task queue under control
4. **Cache templates** - Templates are generated on demand, consider caching
5. **Pagination** - When checking many invoices, paginate results

## Security Checklist

- [ ] API keys in environment variables only
- [ ] Never commit secrets to repository
- [ ] Use HTTPS for all API calls
- [ ] Verify Slack request signatures
- [ ] Validate email addresses before sending
- [ ] Rotate API keys regularly
- [ ] Use least-privilege IAM roles (AWS)
- [ ] Scope Slack bot permissions
- [ ] Review recipient lists for accuracy
