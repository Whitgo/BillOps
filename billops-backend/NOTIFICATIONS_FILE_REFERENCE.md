# BillOps Notification System - File Reference Guide

## 📂 Core Service Files

### Email Service
**File**: `app/services/email.py` (443 lines)
- **Purpose**: Core email sending with provider abstraction
- **Classes**: 
  - `SendGridEmailProvider` - SendGrid implementation
  - `AWSEmailProvider` - AWS SES implementation
  - `EmailService` - Factory selecting correct provider
- **Key Methods**:
  - `send_email()` - Generic email sender
  - `send_invoice_email()` - Invoice with PDF
  - `send_alert_email()` - Styled alerts

### Email Templates
**File**: `app/services/email_templates.py` (716 lines)
- **Purpose**: Professional HTML and text email templates
- **Class**: `EmailTemplates` (static methods)
- **Templates**:
  - `invoice_template()` - Invoice email with items
  - `payment_confirmation_template()` - Payment received
  - `overdue_invoice_template()` - Past-due alert
  - `time_entry_summary_template()` - Daily summary
- **Returns**: `{"html": "...", "text": "..."}`

### Email Notification Service
**File**: `app/services/notifications/email.py` (181 lines)
- **Purpose**: High-level email notification wrapper
- **Class**: `EmailNotificationService`
- **Key Methods**:
  - `send_invoice_notification()`
  - `send_payment_confirmation()`
  - `send_invoice_overdue_alert()`
  - `send_time_entry_reminder()`
  - `send_alert_email()`

### Slack Notification Service
**File**: `app/services/notifications/slack.py` (301 lines)
- **Purpose**: Slack message posting with Block Kit
- **Class**: `SlackNotificationService`
- **Key Methods**:
  - `send_invoice_notification()`
  - `send_payment_notification()`
  - `send_daily_summary()`
  - `send_overdue_invoice_alert()`
  - `send_notification()` - DM notifications
  - `send_message()` - Generic message API

### Slack Message Formatter
**File**: `app/services/slack_message_formatter.py` (614 lines)
- **Purpose**: Block Kit message builders
- **Classes**:
  - `SlackBlockBuilder` - Static methods for blocks
  - `SlackMessageBuilder` - Fluent builder pattern
  - `MessageColor` - Color constants enum
- **Format Functions** (7 total):
  1. `format_invoice_message()`
  2. `format_payment_message()`
  3. `format_time_entry_message()`
  4. `format_daily_summary_message()`
  5. `format_alert_message()`
  6. `format_overdue_invoice_alert()`
  7. `format_invoice_details_message()`

### Celery Tasks
**File**: `app/services/tasks/notifications.py` (411 lines)
- **Purpose**: Async notification delivery tasks
- **Email Tasks**:
  - `send_invoice_email.delay(invoice_id, ...)`
  - `send_payment_email.delay(invoice_id, ...)`
  - `send_overdue_invoice_alert.delay(...)`
- **Slack Tasks**:
  - `send_invoice_slack.delay(invoice_id, ...)`
  - `send_payment_slack.delay(invoice_id, ...)`
- **Scheduled Tasks**:
  - `check_overdue_invoices.delay(user_id)`
  - `send_daily_email_summaries.delay(...)`
  - `send_weekly_invoice_summary.delay(...)`

## 🛣️ API Routes

**File**: `app/api/v1/routes/notifications.py` (357+ lines)
- **Purpose**: FastAPI endpoints for notification management
- **Endpoints**:
  - `POST /send-invoice-email` - Send invoice via email
  - `POST /send-invoice-slack` - Send invoice to Slack
  - `POST /send-payment-email` - Payment confirmation
  - `POST /send-payment-slack` - Payment to Slack
  - `POST /send-alert-email` - Generic alert email
  - `POST /send-alert-slack` - Generic alert to Slack
  - `POST /overdue/check` - Check overdue invoices
  - `POST /test/email` - Test email provider
  - `POST /test/slack` - Test Slack integration
  - `GET /status/{task_id}` - Get Celery task status
  - `GET /config/status` - Show configuration status
  - `GET /health` - Health check

## 🧪 Test Files

**File**: `tests/integration/test_notifications.py` (600+ lines)
- **Purpose**: Comprehensive test suite for all components
- **Test Classes**:
  - `TestEmailService` - Email provider tests (5 tests)
  - `TestEmailTemplates` - Template rendering tests (8 tests)
  - `TestEmailNotificationService` - Email service tests (4 tests)
  - `TestSlackMessageFormatting` - Slack formatting tests (5 tests)
  - `TestSlackNotificationService` - Slack service tests (4 tests)
  - `TestNotificationIntegration` - Integration tests (2 tests)
- **Total**: 29 test cases

**Note**: File at `tests/integration/test_email_slack_notifications.py` also exists (may be legacy)

## 📚 Documentation Files

### Main Documentation
**File**: `NOTIFICATIONS.md` (17 KB)
- Complete technical reference
- Architecture overview
- Component descriptions
- Configuration setup
- API endpoint documentation
- Usage examples
- Error handling guide
- Security considerations
- Monitoring & debugging
- Performance optimization
- Troubleshooting guide

### Quick Reference
**File**: `NOTIFICATIONS_QUICK_REF.md` (9.5 KB)
- Quick start instructions
- Common tasks with code examples
- API endpoint summary table
- Debugging commands
- Troubleshooting quick fixes
- Security checklist

### Integration Guide
**File**: `NOTIFICATIONS_INTEGRATION.md` (14 KB)
- Invoice workflow integration examples
- Running tests procedures
- Manual testing guide
- Testing checklist
- Performance testing
- Debugging guide
- Common issues & solutions
- Deployment checklist
- Future enhancements

### Implementation Summary
**File**: `NOTIFICATIONS_SUMMARY.md` (9.5 KB)
- Overview of completed work
- Component summary
- Architecture diagram
- Configuration reference
- Key features list
- Usage examples
- Next steps for integration
- File structure guide
- Support & questions

### Implementation Checklist
**File**: `NOTIFICATIONS_CHECKLIST.md` (varies)
- Completed tasks checklist
- Implementation statistics
- Features implemented
- Testing coverage
- Security features
- Documentation quality
- Remaining optional tasks
- Quality metrics
- Final status

## ⚙️ Configuration

**File**: `app/config/settings.py`
- **Email Settings**:
  - `email_provider` - "sendgrid" or "ses"
  - `sendgrid_api_key` - SendGrid API key
  - `ses_access_key_id` - AWS access key
  - `ses_secret_access_key` - AWS secret key
  - `ses_region` - AWS region (default: us-east-1)
  - `from_email` - Sender email address
  - `from_name` - Sender display name
- **Slack Settings**:
  - `slack_bot_token` - Bot OAuth token
  - `slack_signing_secret` - Request verification secret
  - `slack_channel_id` - Default channel ID

## 🎯 Quick Navigation

### I need to...

**Send an invoice email**
→ See `app/services/notifications/email.py` + `NOTIFICATIONS_QUICK_REF.md`

**Generate a professional template**
→ See `app/services/email_templates.py` + `NOTIFICATIONS.md` (Usage Examples)

**Post to Slack**
→ See `app/services/notifications/slack.py` + `NOTIFICATIONS_QUICK_REF.md`

**Format a Slack message**
→ See `app/services/slack_message_formatter.py` + Code examples in tests

**Queue an async task**
→ See `app/services/tasks/notifications.py` + `NOTIFICATIONS_INTEGRATION.md`

**Add a notification endpoint**
→ See `app/api/v1/routes/notifications.py` + `NOTIFICATIONS.md` (API Endpoints)

**Integrate with invoice workflow**
→ See `NOTIFICATIONS_INTEGRATION.md` (Integration with Invoice Workflow)

**Set up for production**
→ See `NOTIFICATIONS_INTEGRATION.md` (Deployment Checklist)

**Debug a notification issue**
→ See `NOTIFICATIONS.md` (Troubleshooting) + `NOTIFICATIONS_INTEGRATION.md` (Debugging Guide)

**Write tests**
→ See `tests/integration/test_notifications.py` as examples + `NOTIFICATIONS_INTEGRATION.md` (Testing)

**Understand the architecture**
→ See `NOTIFICATIONS.md` (Architecture) + `NOTIFICATIONS_SUMMARY.md` (Architecture Diagram)

## 📊 File Summary

| Category | File | Size | Status |
|----------|------|------|--------|
| Core Email | app/services/email.py | 443 lines | ✅ Complete |
| Templates | app/services/email_templates.py | 716 lines | ✅ Complete (NEW) |
| Email Notifications | app/services/notifications/email.py | 181 lines | ✅ Complete |
| Slack Notifications | app/services/notifications/slack.py | 301 lines | ✅ Complete |
| Slack Formatting | app/services/slack_message_formatter.py | 614 lines | ✅ Complete |
| Celery Tasks | app/services/tasks/notifications.py | 411 lines | ✅ Complete |
| API Routes | app/api/v1/routes/notifications.py | 357+ lines | ✅ Enhanced |
| Tests | tests/integration/test_notifications.py | 600+ lines | ✅ Complete (NEW) |
| Docs | NOTIFICATIONS.md | 17 KB | ✅ Complete (NEW) |
| Quick Ref | NOTIFICATIONS_QUICK_REF.md | 9.5 KB | ✅ Complete (NEW) |
| Integration | NOTIFICATIONS_INTEGRATION.md | 14 KB | ✅ Complete (NEW) |
| Summary | NOTIFICATIONS_SUMMARY.md | 9.5 KB | ✅ Complete (NEW) |
| Checklist | NOTIFICATIONS_CHECKLIST.md | varies | ✅ Complete (NEW) |

## 🔗 File Dependencies

```
API Routes
    └─→ app/api/v1/routes/notifications.py
         ├─→ EmailNotificationService
         │   └─→ EmailService
         │       ├─→ SendGridEmailProvider
         │       └─→ AWSEmailProvider
         │
         ├─→ SlackNotificationService
         │   └─→ slack_sdk.WebClient
         │
         └─→ Celery Tasks
             └─→ app/services/tasks/notifications.py
```

## 🚀 Getting Started

1. **First Time Setup**:
   - Read `NOTIFICATIONS_QUICK_REF.md` (Quick Start section)
   - Set environment variables
   - Test with `POST /test/email` and `POST /test/slack`

2. **Integration**:
   - Read `NOTIFICATIONS_INTEGRATION.md` (Integration with Invoice Workflow)
   - Update invoice service to call notification tasks
   - Wire up API endpoints

3. **Testing**:
   - Read `NOTIFICATIONS_INTEGRATION.md` (Running Tests)
   - Run `pytest tests/integration/test_notifications.py -v`

4. **Deployment**:
   - Read `NOTIFICATIONS_INTEGRATION.md` (Deployment Checklist)
   - Set environment variables in production
   - Start Celery worker and beat scheduler
   - Monitor task execution

## 📞 Support

All questions answered in documentation:
- **"How do I..."** → Check `NOTIFICATIONS_QUICK_REF.md`
- **"What's the API for..."** → Check `NOTIFICATIONS.md` (API Endpoints)
- **"How do I integrate this..."** → Check `NOTIFICATIONS_INTEGRATION.md`
- **"Why isn't this working..."** → Check `NOTIFICATIONS.md` (Troubleshooting)
- **"What files do I need..."** → You're reading it!
