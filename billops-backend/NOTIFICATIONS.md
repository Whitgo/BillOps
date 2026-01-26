# Notifications System Documentation

## Overview

The BillOps notification system provides comprehensive email and Slack integration for sending invoices, payment confirmations, overdue alerts, and daily time summaries. The system is built with a provider-agnostic architecture supporting both SendGrid and AWS SES for email delivery.

## Architecture

### Service Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    API Routes                               │
│              /api/v1/notifications/*                         │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                  │
┌───────▼──────────┐          ┌──────────▼────────┐
│  Email Service   │          │  Slack Service    │
│  (Notification)  │          │  (Notification)   │
└───────┬──────────┘          └────────┬──────────┘
        │                               │
        │              ┌────────────────┤
        │              │                │
┌───────▼──────────────┴──┐  ┌────────▼──────────┐
│  Email Service Core   │  │ Slack Formatters  │
│  (SendGrid/SES)       │  │ (Block Kit)       │
└──────────────────────┘  └──────────────────┘
```

### Components

#### 1. Email Service (`app/services/email.py`)

Core email sending service with provider abstraction:

**SendGridEmailProvider**
- Uses SendGrid API for email delivery
- Supports attachments (PDF invoices)
- HTML and plain text support
- Full MIME support

**AWSEmailProvider**
- Uses AWS SES for email delivery
- Raw email format with MIME support
- PDF attachment support
- Region configurable (default: us-east-1)

#### 2. Notification Services

**EmailNotificationService** (`app/services/notifications/email.py`)
- High-level wrapper around email service
- Methods:
  - `send_invoice_notification()` - Invoice delivery with PDF
  - `send_payment_confirmation()` - Payment received
  - `send_invoice_overdue_alert()` - Past-due reminder
  - `send_time_entry_reminder()` - Daily time summaries
  - `send_alert_email()` - Generic alerts

**SlackNotificationService** (`app/services/notifications/slack.py`)
- Slack message posting with Block Kit formatting
- Methods:
  - `send_invoice_notification()` - Invoice alerts
  - `send_payment_notification()` - Payment confirmations
  - `send_daily_summary()` - Daily time summaries
  - `send_overdue_invoice_alert()` - Overdue alerts
  - `send_notification()` - Generic DM notifications
  - `send_message()` - Low-level message API

#### 3. Message Formatting (`app/services/slack_message_formatter.py`)

Slack Block Kit builders for composable messages:

**SlackBlockBuilder** - Static methods for individual blocks
- `header()` - Header blocks
- `section()` - Text sections
- `divider()` - Visual dividers
- `context()` - Context information
- `button()` - Interactive buttons
- `actions()` - Action containers
- `fields()` - Field layouts

**SlackMessageBuilder** - Fluent builder for complete messages
- Chainable methods: `add_header()`, `add_section()`, `add_divider()`, `add_fields()`
- Color management with `MessageColor` enum
- `build()` returns complete Slack message dict

**Format Functions** (7 total)
1. `format_invoice_message()` - Invoice notification
2. `format_payment_message()` - Payment confirmation
3. `format_time_entry_message()` - Time entry created
4. `format_daily_summary_message()` - Daily summary
5. `format_alert_message()` - Generic alerts with color coding
6. `format_overdue_invoice_alert()` - Overdue payment alert
7. `format_invoice_details_message()` - Detailed invoice view

#### 4. Email Templates (`app/services/email_templates.py`)

Professional HTML and plain text email templates:

**Template Methods**
1. `invoice_template()` - Professional invoice email
   - Dynamic items table with qty/rate/amount
   - Invoice details grid layout
   - Responsive CSS styling
   - Plain text fallback
   - Returns: `{"html": "...", "text": "..."}`

2. `payment_confirmation_template()` - Payment received
   - Success indicator with green styling
   - Payment details section
   - Professional footer

3. `overdue_invoice_template()` - Past-due reminder
   - Warning indicator with yellow styling
   - Days overdue calculation
   - Amount due highlight
   - Call-to-action styling

4. `time_entry_summary_template()` - Daily time summary
   - Entry count and total hours
   - Optional itemized list
   - Date summary
   - Professional formatting

#### 5. Celery Tasks (`app/services/tasks/notifications.py`)

Async notification delivery with exponential backoff:

**Email Tasks**
- `send_invoice_email()` - Send invoice via email (3 retries)
- `send_payment_email()` - Payment confirmation (2 retries)
- `send_overdue_invoice_alert()` - Overdue alerts (2 retries)

**Slack Tasks**
- `send_invoice_slack()` - Invoice to Slack (3 retries)
- `send_payment_slack()` - Payment to Slack (2 retries)

**Scheduled Tasks**
- `check_overdue_invoices()` - Daily overdue check
- `send_daily_email_summaries()` - Daily time summaries
- `send_weekly_invoice_summary()` - Weekly stats

## Configuration

### Environment Variables

**Email Configuration**
```
EMAIL_PROVIDER=sendgrid  # or "ses"
SENDGRID_API_KEY=sg_...
SES_ACCESS_KEY_ID=AKIA...
SES_SECRET_ACCESS_KEY=...
SES_REGION=us-east-1
FROM_EMAIL=noreply@billops.com
FROM_NAME=BillOps
```

**Slack Configuration**
```
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_CHANNEL_ID=C123456...
```

### Settings (`app/config/settings.py`)

All configuration is loaded from environment and managed centrally:

```python
from app.config.settings import Settings

settings = Settings()
settings.email_provider  # "sendgrid" or "ses"
settings.sendgrid_api_key
settings.slack_bot_token
settings.from_email
# ... etc
```

## API Endpoints

### Invoice Notifications

**Send Invoice**
```
POST /api/v1/notifications/send-invoice-email
Parameters:
  - invoice_id: UUID of invoice
  - recipient_email: Email address
Returns:
  - message: Status message
  - success: Boolean
```

**Send Invoice to Slack**
```
POST /api/v1/notifications/send-invoice-slack
Parameters:
  - invoice_id: UUID of invoice
  - channel: Slack channel ID
  - slack_bot_token: (optional) Bot token
Returns:
  - message: Status message
  - success: Boolean
```

### Payment Notifications

**Send Payment Confirmation (Email)**
```
POST /api/v1/notifications/send-payment-email
Parameters:
  - invoice_id: UUID
  - recipient_email: Email address
  - payment_amount_cents: Amount in cents
Returns:
  - message: Status message
  - success: Boolean
```

**Send Payment Confirmation (Slack)**
```
POST /api/v1/notifications/send-payment-slack
Parameters:
  - invoice_id: UUID
  - channel: Slack channel ID
  - payment_amount_cents: Amount in cents
  - slack_bot_token: (optional) Bot token
Returns:
  - message: Status message
  - success: Boolean
```

### Alerts

**Check Overdue Invoices**
```
POST /api/v1/notifications/overdue/check
Returns:
  - message: Status message
  - success: Boolean
  - Triggers: Celery task to check all overdue invoices
```

**Send Alert Email**
```
POST /api/v1/notifications/send-alert-email
Parameters:
  - recipient_email: Email address
  - alert_title: Alert title
  - alert_message: Alert message
  - alert_type: info | warning | error
Returns:
  - message: Status message
  - success: Boolean
```

**Send Alert to Slack**
```
POST /api/v1/notifications/send-alert-slack
Parameters:
  - channel: Slack channel ID
  - alert_title: Alert title
  - alert_message: Alert message
  - alert_type: info | warning | error
  - slack_bot_token: (optional) Bot token
Returns:
  - message: Status message
  - success: Boolean
```

### Testing & Status

**Test Email Provider**
```
POST /api/v1/notifications/test/email?recipient_email=test@example.com
Returns:
  - message: Status message
  - success: Boolean
  - Validates email provider configuration
```

**Test Slack Integration**
```
POST /api/v1/notifications/test/slack?channel=C123456
Returns:
  - message: Status message
  - success: Boolean
  - Validates Slack bot token and channel access
```

**Get Task Status**
```
GET /api/v1/notifications/status/{task_id}
Returns:
  - task_id: Celery task ID
  - state: PENDING | STARTED | SUCCESS | FAILURE | RETRY
  - status: Task progress message
  - error: (if failed) Error message
  - result: (if succeeded) Task result
```

**Configuration Status**
```
GET /api/v1/notifications/config/status
Returns:
  - email:
    - provider: sendgrid | ses
    - configured: Boolean
    - from_email: Email address
  - slack:
    - configured: Boolean
    - signing_secret_configured: Boolean
```

**Health Check**
```
GET /api/v1/notifications/health
Returns:
  - message: "Notification service is healthy"
  - success: true
```

## Usage Examples

### Sending an Invoice

```python
from app.services.notifications.email import EmailNotificationService

email_service = EmailNotificationService()

# Send invoice email
success = email_service.send_invoice_notification(
    recipient_email="client@example.com",
    recipient_name="Acme Corp",
    invoice_number="INV-2024-001",
    invoice_total_cents=150000,  # $1,500.00
    invoice_html=invoice_html,
    due_date=datetime(2024, 2, 15),
)
```

### Sending Slack Notification

```python
from app.services.notifications.slack import SlackNotificationService

slack_service = SlackNotificationService(bot_token="xoxb-...")

# Send invoice to Slack
success = slack_service.send_invoice_notification(
    channel="C123456",
    invoice_number="INV-2024-001",
    client_name="Acme Corp",
    amount_cents=150000,
    status="sent",
)
```

### Using Email Templates

```python
from app.services.email_templates import EmailTemplates

# Generate invoice email
templates = EmailTemplates.invoice_template(
    client_name="Acme Corp",
    invoice_number="INV-2024-001",
    invoice_date=datetime(2024, 1, 15),
    due_date=datetime(2024, 2, 15),
    total_amount=1500.00,
    currency="USD",
)

html_content = templates["html"]
text_content = templates["text"]
```

### Queuing Async Tasks

```python
from app.services.tasks.notifications import send_invoice_email

# Queue email task (async)
task = send_invoice_email.delay(
    invoice_id="550e8400-e29b-41d4-a716-446655440000",
    recipient_email="client@example.com",
    recipient_name="Acme Corp",
)

# Check task status
task_result = celery_app.AsyncResult(task.id)
print(task_result.state)  # PENDING, STARTED, SUCCESS, FAILURE
print(task_result.info)   # Progress or error info
```

## Error Handling

### Graceful Degradation

The notification system is designed to fail gracefully:

1. **Email Provider Failure** - Falls back to configured backup
2. **Slack Unavailable** - Returns False, logs error, doesn't block invoice flow
3. **Missing Configuration** - Detects at startup, prevents sending
4. **Invalid Recipients** - Validates before sending, returns False

### Logging

All operations are logged with context:

```python
import logging
logger = logging.getLogger(__name__)

# Successful send
logger.info(f"Invoice {invoice_id} sent to {email}")

# Failed send with retry
logger.warning(f"Failed to send invoice {invoice_id}, retrying...")

# Configuration error
logger.error(f"Email provider misconfigured: {error}")
```

## Security Considerations

### API Key Protection

- Store API keys in environment variables only
- Never commit keys to repository
- Rotate keys regularly
- Use least-privilege IAM roles

### Slack Security

- Verify request signatures with signing secret
- Validate timestamp (5-minute window)
- Use bot tokens with minimal required scopes
- Scope permissions to specific channels

### Email Security

- Validate recipient email addresses
- Sanitize template variables
- HTTPS only for email delivery
- Use TLS for SMTP connections

## Monitoring & Debugging

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Monitor Celery Tasks

```bash
# Watch Celery tasks
celery -A app.celery_app events

# Inspect task queue
celery -A app.celery_app inspect active
```

### Check Notification Config

```bash
curl http://localhost:8000/api/v1/notifications/config/status
```

### Test Email Provider

```bash
curl -X POST http://localhost:8000/api/v1/notifications/test/email \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "recipient_email=test@example.com"
```

### Test Slack Integration

```bash
curl -X POST http://localhost:8000/api/v1/notifications/test/slack \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "channel=C123456"
```

## Performance Considerations

### Async Delivery

All notifications are queued via Celery for async processing:
- Email delivery doesn't block API responses
- Slack posting happens in background worker
- Retry logic handles transient failures

### Rate Limiting

Consider implementing rate limits:
- Email: 100 per hour per recipient
- Slack: 50 per minute per channel
- Configurable in settings

### Batch Operations

For bulk notifications:

```python
from app.services.tasks.notifications import check_overdue_invoices

# Trigger check for all overdue invoices
task = check_overdue_invoices.delay(user_id=user_id)
```

## Troubleshooting

### Emails Not Sending

1. **Check configuration**
   ```bash
   GET /api/v1/notifications/config/status
   ```

2. **Test email provider**
   ```bash
   POST /api/v1/notifications/test/email?recipient_email=test@example.com
   ```

3. **Check Celery worker**
   ```bash
   celery -A app.celery_app inspect active
   ```

4. **Review logs**
   ```bash
   tail -f logs/app.log | grep notification
   ```

### Slack Messages Not Posting

1. **Verify bot token**
   - Token should start with `xoxb-`
   - Check in Slack workspace settings

2. **Check channel access**
   - Bot must be added to channel
   - Use `/invite @billops` in Slack

3. **Test integration**
   ```bash
   POST /api/v1/notifications/test/slack?channel=C123456
   ```

4. **Verify permissions**
   - Bot needs `chat:write` permission
   - Channel must exist and be accessible

### Task Not Executing

1. **Check Celery worker is running**
   ```bash
   ps aux | grep celery
   ```

2. **Verify Redis/broker is available**
   ```bash
   redis-cli ping
   ```

3. **Check task queue**
   ```bash
   celery -A app.celery_app inspect active_queues
   ```

4. **Review worker logs**
   ```bash
   tail -f logs/celery.log
   ```

## Testing

### Unit Tests

```bash
pytest tests/integration/test_notifications.py -v
```

### Test Email Template

```python
from app.services.email_templates import EmailTemplates

templates = EmailTemplates.invoice_template(
    client_name="Test Client",
    invoice_number="TEST-001",
    invoice_date=datetime.now(),
    due_date=None,
    total_amount=1000.00,
)

assert "html" in templates
assert "TEST-001" in templates["html"]
print(templates["html"])  # View generated HTML
```

### Test Slack Message

```python
from app.services.slack_message_formatter import format_invoice_message

message = format_invoice_message(
    invoice_number="TEST-001",
    client_name="Test Client",
    amount=1000.00,
    status="sent",
)

assert "blocks" in message
print(json.dumps(message, indent=2))
```

## Future Enhancements

- [ ] SMS notifications
- [ ] Push notifications for mobile app
- [ ] Email templates in database (CMS)
- [ ] A/B testing email templates
- [ ] Message scheduling/delivery optimization
- [ ] Webhook integration for third-party services
- [ ] Notification preferences per client
- [ ] Message preview API
- [ ] Delivery analytics and reporting
