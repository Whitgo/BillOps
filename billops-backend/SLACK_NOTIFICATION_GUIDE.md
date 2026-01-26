# Slack Notification Guide

## Overview

The Slack Notification Service provides rich, formatted notifications using Slack's Block Kit API. Supports invoices, payments, time tracking, daily summaries, and custom alerts.

## Architecture

### Core Components

1. **SlackBlockBuilder**: Low-level Block Kit element builder
2. **SlackMessageBuilder**: High-level message composition with chainable API
3. **Message Formatters**: Application-specific message templates
4. **SlackNotificationService**: High-level notification interface

### Message Formatting

All messages use Slack's Block Kit for rich formatting:

```
Header
├─ Section with fields
├─ Divider
├─ Context with metadata
├─ Action buttons
└─ Footer
```

## Configuration

Set Slack bot token via environment variable:

```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_WORKSPACE_ID=T00000000  # Optional: workspace ID
SLACK_DEFAULT_CHANNEL=#billing  # Optional: default channel
```

### Creating a Slack Bot

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Create New App → From scratch
3. Name: "BillOps"
4. Under "Bot Token Scopes" add:
   - `chat:write` - Send messages
   - `chat:write.public` - Post in public channels
5. Copy Bot User OAuth Token (xoxb-...)
6. Install app to your workspace

## Slack Message Formatter API

### Block Building

#### SlackBlockBuilder

Low-level Block Kit builder:

```python
from app.services.slack_message_formatter import SlackBlockBuilder

# Header
header = SlackBlockBuilder.header("Invoice Alert")

# Section with markdown
section = SlackBlockBuilder.section(
    "*Invoice #INV-001*\nAmount: $1,500.00",
    markdown=True
)

# Button element
button = SlackBlockBuilder.button(
    text="View Invoice",
    action_id="btn_view_invoice",
    value="INV-001",
    url="https://billops.com/invoices/INV-001"
)

# Context with emoji and timestamp
context = SlackBlockBuilder.context(
    [
        "🔔",
        "Posted: 2024-01-15 10:30 AM"
    ]
)

# Fields (key-value pairs)
fields = SlackBlockBuilder.fields([
    ("Invoice #", "INV-001"),
    ("Amount", "$1,500.00"),
    ("Due Date", "2024-02-15"),
    ("Status", "Sent")
])
```

### Message Building

#### SlackMessageBuilder

High-level chainable message builder:

```python
from app.services.slack_message_formatter import (
    SlackMessageBuilder,
    MessageColor,
)

message = (
    SlackMessageBuilder()
    .add_header("Invoice Notification")
    .add_section("*Invoice #INV-001* has been sent", markdown=True)
    .add_divider()
    .add_fields([
        ("Amount", "$1,500.00"),
        ("Client", "Acme Corp"),
        ("Due Date", "2024-02-15"),
    ])
    .add_buttons([
        {
            "text": "View",
            "action_id": "view_invoice",
            "value": "INV-001",
            "style": "primary"
        },
        {
            "text": "Pay Now",
            "action_id": "pay_invoice",
            "value": "INV-001",
            "style": "danger"
        }
    ])
    .add_context("Sent to client@example.com")
    .set_color(MessageColor.SUCCESS)
    .build()
)
```

Available colors:
- `MessageColor.SUCCESS` - Green (#36a64f)
- `MessageColor.WARNING` - Yellow (#ff9900)
- `MessageColor.ERROR` - Red (#ff0000)
- `MessageColor.INFO` - Blue (#0099ff)
- `MessageColor.NEUTRAL` - Gray (#999999)

## Message Formatters

Ready-to-use formatters for common notification types:

### Invoice Notification

```python
from app.services.slack_message_formatter import format_invoice_message

message = format_invoice_message(
    invoice_number="INV-001",
    client_name="Acme Corp",
    amount=1500.00,
    status="sent",  # sent, overdue, paid
    due_date="2024-02-15"  # Optional
)
```

Output: Professional invoice notification with status badge and amount.

### Payment Notification

```python
from app.services.slack_message_formatter import format_payment_message

message = format_payment_message(
    invoice_number="INV-001",
    client_name="Acme Corp",
    amount=1500.00,
    payment_date="2024-01-20",  # Optional
    payment_method="ACH"  # Optional
)
```

Output: Payment confirmation with invoice details.

### Time Entry Notification

```python
from app.services.slack_message_formatter import format_time_entry_message

message = format_time_entry_message(
    description="Client meeting",
    duration_hours=2.5,
    project_name="Project A",
    entry_date="2024-01-15"  # Optional
)
```

Output: Time entry log with hours and project.

### Daily Summary

```python
from app.services.slack_message_formatter import format_daily_summary_message

message = format_daily_summary_message(
    total_hours=8.0,
    entry_count=4,
    summary_date="2024-01-15"  # Optional
)
```

Output: Daily time tracking summary with progress bar.

### Alert Notification

```python
from app.services.slack_message_formatter import format_alert_message

message = format_alert_message(
    title="System Alert",
    message="High invoice overdue count detected",
    alert_type="warning",  # info, warning, error
    details=None  # Optional dict of details
)
```

Output: Alert with appropriate color coding.

### Overdue Invoice Alert

```python
from app.services.slack_message_formatter import format_overdue_invoice_alert

message = format_overdue_invoice_alert(
    invoice_number="INV-001",
    client_name="Acme Corp",
    amount=1500.00,
    days_overdue=5
)
```

Output: Overdue alert with warning styling.

## Slack Notification Service

### SlackNotificationService Class

High-level service for sending formatted Slack messages:

```python
from app.services.notifications.slack import SlackNotificationService

service = SlackNotificationService()  # Uses SLACK_BOT_TOKEN
# Or with custom token:
service = SlackNotificationService("xoxb-custom-token")
```

#### Methods

**send_message()**
```python
def send_message(channel: str, message: dict) -> bool:
    """
    Send a Slack message to a channel.
    
    Args:
        channel: Channel ID (#channel or U00000000)
        message: Message dict with 'blocks' and 'text'
    
    Returns:
        bool: True if successful
    """
```

**send_invoice_notification()**
```python
def send_invoice_notification(
    channel: str,
    invoice_number: str,
    client_name: str,
    amount_cents: int,
    status: str = "sent",  # sent, overdue, paid
    due_date: str = None,
) -> bool:
    """Send formatted invoice notification."""
```

**send_payment_notification()**
```python
def send_payment_notification(
    channel: str,
    invoice_number: str,
    client_name: str,
    amount_cents: int,
    payment_date: str = None,
    payment_method: str = None,
) -> bool:
    """Send formatted payment notification."""
```

**send_time_entry_notification()**
```python
def send_time_entry_notification(
    channel: str,
    description: str,
    duration_hours: float,
    project_name: str,
    entry_date: str = None,
) -> bool:
    """Send formatted time entry notification."""
```

**send_daily_summary()**
```python
def send_daily_summary(
    channel: str,
    total_hours: float,
    entry_count: int,
    summary_date: str = None,
) -> bool:
    """Send daily time summary."""
```

**send_alert()**
```python
def send_alert(
    channel: str,
    title: str,
    message: str,
    alert_type: str = "info",  # info, warning, error
    details: dict = None,
) -> bool:
    """Send generic alert."""
```

**send_overdue_invoice_alert()**
```python
def send_overdue_invoice_alert(
    channel: str,
    invoice_number: str,
    client_name: str,
    amount_cents: int,
    days_overdue: int,
) -> bool:
    """Send overdue invoice alert."""
```

**send_invoice_details()**
```python
def send_invoice_details(
    channel: str,
    invoice_number: str,
    client_name: str,
    amount_cents: int,
    line_items: list[dict],
    due_date: str = None,
) -> bool:
    """Send detailed invoice information."""
```

## Usage Examples

### Basic Message Sending

```python
from app.services.notifications.slack import SlackNotificationService
from app.services.slack_message_formatter import format_invoice_message

service = SlackNotificationService()

message = format_invoice_message(
    invoice_number="INV-001",
    client_name="Acme Corp",
    amount=1500.00,
    status="sent"
)

# Send to channel
success = service.send_message("#billing", message)
if success:
    print("Message sent!")
```

### Invoice Notification

```python
service = SlackNotificationService()

service.send_invoice_notification(
    channel="#billing",
    invoice_number="INV-001",
    client_name="Acme Corp",
    amount_cents=150000,  # $1,500.00
    status="sent",
    due_date="2024-02-15"
)
```

### Overdue Alert

```python
service = SlackNotificationService()

service.send_overdue_invoice_alert(
    channel="#alerts",
    invoice_number="INV-001",
    client_name="Acme Corp",
    amount_cents=150000,
    days_overdue=5
)
```

### Daily Summary

```python
service = SlackNotificationService()

service.send_daily_summary(
    channel="#time-tracking",
    total_hours=8.5,
    entry_count=4,
    summary_date="2024-01-15"
)
```

### Custom Message

```python
from app.services.slack_message_formatter import (
    SlackMessageBuilder,
    MessageColor,
)

message = (
    SlackMessageBuilder()
    .add_header("🎉 Milestone Achievement")
    .add_section("Total invoices sent this month: **50**")
    .add_section("Total revenue: **$75,000**")
    .add_divider()
    .add_buttons([
        {
            "text": "View Dashboard",
            "action_id": "view_dashboard",
            "value": "monthly",
            "style": "primary"
        }
    ])
    .set_color(MessageColor.SUCCESS)
    .build()
)

service = SlackNotificationService()
service.send_message("#announcements", message)
```

## Celery Integration

Send Slack messages asynchronously:

```python
from app.services.tasks.notifications import send_invoice_slack

# Queue Slack notification task
send_invoice_slack.delay(
    invoice_id="uuid-string",
    channel="#billing",
    slack_bot_token=None  # Uses default from env if None
)
```

See [NOTIFICATIONS_QUICK_START.md](NOTIFICATIONS_QUICK_START.md) for Celery task documentation.

## Block Kit Reference

### Block Types

- `header`: Large text header
- `section`: Text with optional image
- `divider`: Visual separator
- `context`: Small text with metadata
- `actions`: Action buttons
- `image`: Display image

### Styling

**Text Formatting**
- `*bold*` - Bold text
- `_italic_` - Italic text
- `~strikethrough~` - Strikethrough
- `` `code` `` - Code block
- `>quote` - Quote block

**Emojis**
```python
message = format_alert_message(
    title="📊 Report Ready",
    message="Invoice report is ready for download",
    alert_type="info"
)
```

Available emojis:
- 📊 Reports/Analytics
- 📧 Email/Messages
- 💰 Payment/Money
- ⏰ Time/Schedule
- ✅ Success/Complete
- ⚠️ Warning
- ❌ Error
- 🔔 Notification

## Testing

Unit tests available in `tests/integration/test_email_slack_notifications.py`:

```bash
# Test Slack block builders
pytest tests/integration/test_email_slack_notifications.py::TestSlackBlockBuilder -v

# Test message builders
pytest tests/integration/test_email_slack_notifications.py::TestSlackMessageBuilder -v

# Test message formatters
pytest tests/integration/test_email_slack_notifications.py::TestMessageFormatters -v

# Test Slack service
pytest tests/integration/test_email_slack_notifications.py::TestSlackNotificationService -v
```

## Troubleshooting

### "invalid_auth" Error

- Verify SLACK_BOT_TOKEN is correct
- Check bot token starts with "xoxb-"
- Verify bot is installed in workspace

### "channel_not_found" Error

- Use channel ID (C00000000) or name (#channel)
- Ensure bot is member of channel
- For direct messages, use user ID (U00000000)

### "not_in_channel" Error

- Invite bot to channel: `/invite @BillOps`
- Or use chat:write.public scope for public channels

### Message not sending

- Check message JSON structure
- Verify blocks field contains valid Block Kit objects
- Look for errors in logs: `logger.error(f"Slack error: {e}")`

## Production Deployment

1. **Secure token**
   ```bash
   export SLACK_BOT_TOKEN="xoxb-your-token"
   # Or use secret manager
   ```

2. **Configure channels**
   ```bash
   export SLACK_DEFAULT_CHANNEL="#billing"
   export SLACK_ALERTS_CHANNEL="#alerts"
   ```

3. **Monitor delivery**
   - Check Slack app activity log
   - Monitor application logs for send errors
   - Set up Slack error webhooks if needed

4. **Rate limiting**
   - Slack allows 1 message/second per channel (bursty)
   - Queue messages using Celery for high volume

## API Reference

For advanced Block Kit features, see [Slack Block Kit Documentation](https://api.slack.com/block-kit).
