# Notifications Integration & Testing Guide

## Integration with Invoice Workflow

### Automatic Invoice Notifications

To automatically send invoice notifications when an invoice is created or sent, update the invoice service:

```python
# app/services/invoices/invoice_service.py

from app.services.tasks.notifications import send_invoice_email, send_invoice_slack
from app.config.settings import Settings

class InvoiceService:
    def create_invoice(self, invoice_data, db):
        """Create invoice and optionally send notification."""
        invoice = Invoice(**invoice_data)
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice
    
    def send_invoice(self, invoice_id, db):
        """Send invoice notification via email and Slack."""
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        # Queue email notification
        if invoice.client and invoice.client.email:
            send_invoice_email.delay(
                invoice_id=str(invoice.id),
                recipient_email=invoice.client.email,
                recipient_name=invoice.client.name,
            )
        
        # Queue Slack notification
        settings = Settings()
        if settings.slack_bot_token and hasattr(invoice.client, 'slack_channel_id'):
            send_invoice_slack.delay(
                invoice_id=str(invoice.id),
                channel=invoice.client.slack_channel_id,
            )
        
        # Update invoice status
        invoice.status = "sent"
        db.commit()
        return invoice
    
    def mark_payment_received(self, invoice_id, payment_amount_cents, db):
        """Mark invoice as paid and send payment confirmation."""
        from app.services.tasks.notifications import send_payment_email, send_payment_slack
        
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        # Record payment
        invoice.status = "paid"
        invoice.paid_date = datetime.now(timezone.utc)
        db.commit()
        
        # Queue payment notification email
        if invoice.client and invoice.client.email:
            send_payment_email.delay(
                invoice_id=str(invoice.id),
                recipient_email=invoice.client.email,
                recipient_name=invoice.client.name,
                payment_amount_cents=payment_amount_cents,
            )
        
        # Queue payment notification to Slack
        if settings.slack_bot_token and hasattr(invoice.client, 'slack_channel_id'):
            send_payment_slack.delay(
                invoice_id=str(invoice.id),
                channel=invoice.client.slack_channel_id,
                payment_amount_cents=payment_amount_cents,
            )
        
        return invoice
```

### Invoice API Endpoint Integration

Update invoice endpoints to trigger notifications:

```python
# app/api/v1/routes/invoices.py

from app.services.tasks.notifications import send_invoice_email

@router.post("/invoices/{invoice_id}/send")
async def send_invoice(
    invoice_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send invoice to client via email and Slack."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Generate invoice PDF
    from app.services.invoices.pdf_generator import generate_invoice_pdf
    pdf_bytes = generate_invoice_pdf(invoice)
    
    # Queue notification
    task = send_invoice_email.delay(
        invoice_id=str(invoice.id),
        recipient_email=invoice.client.email,
        recipient_name=invoice.client.name,
        pdf_content=pdf_bytes,  # Will be passed to email service
    )
    
    return {
        "message": "Invoice sent successfully",
        "task_id": task.id,
        "invoice_id": str(invoice.id),
    }

@router.post("/invoices/{invoice_id}/mark-paid")
async def mark_invoice_paid(
    invoice_id: str,
    payment_amount_cents: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark invoice as paid and send payment confirmation."""
    from app.services.tasks.notifications import send_payment_email
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice.status = "paid"
    invoice.paid_date = datetime.now(timezone.utc)
    db.commit()
    
    # Queue payment confirmation
    task = send_payment_email.delay(
        invoice_id=str(invoice.id),
        recipient_email=invoice.client.email,
        recipient_name=invoice.client.name,
        payment_amount_cents=payment_amount_cents,
    )
    
    return {
        "message": "Invoice marked as paid",
        "task_id": task.id,
        "invoice_id": str(invoice.id),
    }
```

## Running Tests

### Unit Tests

```bash
# Run notification tests
pytest tests/integration/test_notifications.py -v

# Run specific test class
pytest tests/integration/test_notifications.py::TestEmailService -v

# Run specific test
pytest tests/integration/test_notifications.py::TestEmailService::test_sendgrid_email_provider_initialization -v

# Run with coverage
pytest tests/integration/test_notifications.py --cov=app.services.notifications --cov-report=html
```

### Test Coverage Report

```bash
# Generate coverage report
pytest tests/integration/test_notifications.py --cov=app.services.notifications --cov-report=term-missing

# Open HTML report
open htmlcov/index.html
```

### Manual Testing

```bash
# Test email configuration
curl -X POST http://localhost:8000/api/v1/notifications/test/email \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "recipient_email=test@example.com"

# Test Slack configuration
curl -X POST http://localhost:8000/api/v1/notifications/test/slack \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "channel=C123456789"

# Check configuration status
curl http://localhost:8000/api/v1/notifications/config/status
```

### Interactive Testing in Python Shell

```python
# Start Python shell with app context
python -c "
from app.services.email_templates import EmailTemplates
from datetime import datetime

# Test invoice template
templates = EmailTemplates.invoice_template(
    client_name='Test Client',
    invoice_number='TEST-001',
    invoice_date=datetime.now(),
    due_date=None,
    total_amount=1500.00,
)

print('HTML length:', len(templates['html']))
print('Text length:', len(templates['text']))
print('Content OK:', 'TEST-001' in templates['html'])
"
```

## Testing Checklist

### Email Service Tests ✓
- [x] SendGrid provider initialization
- [x] Email sending via SendGrid
- [x] AWS SES provider initialization
- [x] Email sending via SES
- [x] Provider selection based on config
- [x] Email with attachments
- [x] Multiple recipients
- [x] HTML and text content

### Email Template Tests ✓
- [x] Invoice template generation
- [x] Invoice template with line items
- [x] Payment confirmation template
- [x] Overdue invoice template
- [x] Time entry summary template
- [x] Currency formatting
- [x] Date formatting
- [x] HTML and text versions

### Email Notification Service Tests ✓
- [x] Send invoice notification
- [x] Send payment confirmation
- [x] Send overdue alert
- [x] Send time entry reminder
- [x] Error handling

### Slack Message Formatting Tests ✓
- [x] SlackMessageBuilder
- [x] format_invoice_message()
- [x] format_payment_message()
- [x] format_daily_summary_message()
- [x] Message color coding

### Slack Notification Service Tests ✓
- [x] Send invoice notification to Slack
- [x] Send payment notification to Slack
- [x] Graceful failure without token
- [x] Send overdue alert to Slack
- [x] Error handling

### Integration Tests ✓
- [x] Complete invoice workflow (email + Slack)
- [x] Complete payment workflow (email + Slack)

## Performance Testing

### Load Test Email Service

```python
import time
from app.services.notifications.email import EmailNotificationService

service = EmailNotificationService()
start = time.time()

# Send 100 emails (async via tasks)
for i in range(100):
    from app.services.tasks.notifications import send_invoice_email
    send_invoice_email.delay(
        invoice_id=f"invoice-{i}",
        recipient_email=f"test{i}@example.com",
        recipient_name=f"Client {i}",
    )

elapsed = time.time() - start
print(f"Queued 100 emails in {elapsed:.2f}s")
```

### Monitor Celery Queue

```bash
# Watch queue in real-time
celery -A app.celery_app events

# Check active tasks
celery -A app.celery_app inspect active

# Check pending tasks
celery -A app.celery_app inspect reserved

# Get worker stats
celery -A app.celery_app inspect stats
```

## Debugging Guide

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("app.services.notifications").setLevel(logging.DEBUG)
```

### Inspect Celery Task

```python
from app.celery_app import celery_app
from app.services.tasks.notifications import send_invoice_email

# Queue task
task = send_invoice_email.delay(
    invoice_id="test-123",
    recipient_email="test@example.com",
    recipient_name="Test Client",
)

# Inspect task
result = celery_app.AsyncResult(task.id)
print(f"Task ID: {task.id}")
print(f"State: {result.state}")
print(f"Info: {result.info}")

# Wait for completion
result.wait()
print(f"Result: {result.result}")
```

### Check Email Provider Connection

```python
from app.config.settings import Settings
from app.services.email import EmailService

settings = Settings()
service = EmailService()

# Test sending
try:
    success = service.send_email(
        to_email="test@example.com",
        subject="Test Email",
        html_content="<h1>Test</h1>",
    )
    print(f"Email sent successfully: {success}")
except Exception as e:
    print(f"Error: {e}")
```

### Check Slack Connection

```python
from app.config.settings import Settings
from app.services.notifications.slack import SlackNotificationService

settings = Settings()
service = SlackNotificationService(bot_token=settings.slack_bot_token)

# Test message
try:
    success = service.send_message(
        channel="C123456",
        text="Test message from BillOps",
    )
    print(f"Slack message sent: {success}")
except Exception as e:
    print(f"Error: {e}")
```

## Common Issues & Solutions

### Issue: Emails not sending

**Symptoms:** Tasks queued but emails not received

**Solutions:**
1. Verify Celery worker is running: `ps aux | grep celery`
2. Check Redis connection: `redis-cli ping`
3. Review task logs: `celery -A app.celery_app inspect active`
4. Test email provider: `POST /test/email`
5. Check configuration: `GET /config/status`

### Issue: Slack messages failing silently

**Symptoms:** Slack tasks succeed but no messages appear

**Solutions:**
1. Verify bot token is valid: `GET /config/status`
2. Verify bot is added to channel: Check Slack workspace
3. Check permissions: Bot needs `chat:write`
4. Test Slack integration: `POST /test/slack`
5. Review logs for errors

### Issue: Template rendering fails

**Symptoms:** Email sent but content is broken

**Solutions:**
1. Verify template parameters are complete
2. Check for special characters in dynamic content
3. Validate HTML email in preview tool
4. Test template directly in Python
5. Review error logs for rendering errors

### Issue: High task execution time

**Symptoms:** Emails/Slack messages delayed

**Solutions:**
1. Check Celery worker CPU/memory
2. Monitor API provider latency
3. Increase worker concurrency: `celery -A app.celery_app worker --concurrency=4`
4. Use multiple workers: `celery -A app.celery_app worker -Q priority --concurrency=4`
5. Implement task batching for bulk sends

## Deployment Checklist

- [ ] Set EMAIL_PROVIDER environment variable (sendgrid or ses)
- [ ] Set email provider API key (SENDGRID_API_KEY or SES credentials)
- [ ] Set FROM_EMAIL and FROM_NAME
- [ ] Test email provider: `POST /test/email`
- [ ] Set SLACK_BOT_TOKEN (optional, for Slack integration)
- [ ] Set SLACK_SIGNING_SECRET (optional, for Slack webhooks)
- [ ] Test Slack integration: `POST /test/slack`
- [ ] Verify Celery worker is running in production
- [ ] Verify Redis/message broker is running
- [ ] Configure monitoring for task failures
- [ ] Set up log aggregation for notification errors
- [ ] Test end-to-end invoice workflow
- [ ] Test payment notification workflow
- [ ] Verify rate limits are appropriate
- [ ] Review security settings (API key rotation, etc.)

## Performance Benchmarks

**Typical Performance Metrics:**

- Email send via Celery: 50-200ms (async, doesn't block)
- Slack message post: 100-300ms
- Template rendering: 5-20ms
- Task queue processing: <1s for most emails
- Batch operations (100 invoices): ~30-60 seconds

**Optimization Tips:**

1. Use async tasks (Celery) for all notifications
2. Batch similar operations (e.g., daily summaries)
3. Cache rendered templates if sending same template repeatedly
4. Use Slack webhooks instead of API for high-volume posting
5. Implement exponential backoff for retries

## Future Enhancements

- [ ] SMS notifications via Twilio
- [ ] Push notifications for mobile app
- [ ] Message templates stored in database (CMS)
- [ ] A/B testing for email templates
- [ ] Advanced scheduling (send at specific time)
- [ ] Delivery analytics and reporting
- [ ] Message preview API
- [ ] Webhook integration for third-party services
- [ ] Notification preferences per client
- [ ] Email bounce handling
