# Integration Quick Reference

## Getting Started

### 1. Set Environment Variables

```bash
# Google Calendar
export GOOGLE_CLIENT_ID=your_id.apps.googleusercontent.com
export GOOGLE_CLIENT_SECRET=your_secret
export GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/integrations/google/callback

# Outlook Calendar
export MICROSOFT_CLIENT_ID=your_id
export MICROSOFT_CLIENT_SECRET=your_secret
export MICROSOFT_TENANT_ID=common
export MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/integrations/microsoft/callback

# Slack
export SLACK_CLIENT_ID=your_id
export SLACK_CLIENT_SECRET=your_secret
export SLACK_REDIRECT_URI=http://localhost:8000/api/v1/integrations/slack/callback
export SLACK_BOT_TOKEN=xoxb-your-token
export SLACK_SIGNING_SECRET=your_secret
export SLACK_APP_ID=your_app_id
```

### 2. Start Services

```bash
# Terminal 1: API Server
python -m uvicorn app.main:app --reload

# Terminal 2: Celery Worker
celery -A app.celery_app worker --loglevel=info

# Terminal 3: Celery Beat (Scheduler)
celery -A app.celery_app beat --loglevel=info
```

### 3. Test Flow

```bash
# Get Google auth URL
curl http://localhost:8000/api/v1/integrations/google/authorize | jq .

# User visits returned auth_url and grants permission
# Copy the authorization code from redirect

# Exchange code for tokens
curl -X POST http://localhost:8000/api/v1/integrations/google/callback \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"code": "YOUR_AUTH_CODE"}'

# Response includes calendars and oauth_account_id
# Select a calendar
curl -X POST http://localhost:8000/api/v1/integrations/google/select-calendar \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "calendar_id": "primary",
    "calendar_name": "My Calendar",
    "oauth_account_id": "UUID_FROM_CALLBACK"
  }'

# Manual sync
curl -X POST http://localhost:8000/api/v1/integrations/google/{CALENDAR_ID}/sync \
  -H "Authorization: Bearer YOUR_JWT"
```

## Common Tasks

### View Integrated Calendars

```bash
curl http://localhost:8000/api/v1/integrations/calendars \
  -H "Authorization: Bearer YOUR_JWT" | jq .
```

### View Synced Events

```bash
curl http://localhost:8000/api/v1/integrations/calendars/{CALENDAR_ID}/events \
  -H "Authorization: Bearer YOUR_JWT" | jq .
```

### Convert Event to Time Entry

```bash
curl -X POST http://localhost:8000/api/v1/integrations/calendars/events/convert \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "synced_event_id": "UUID",
    "project_id": "UUID (optional)",
    "client_id": "UUID (optional)"
  }'
```

### Enable/Disable Calendar Sync

```bash
curl -X PUT http://localhost:8000/api/v1/integrations/calendars/{CALENDAR_ID}/enable \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"sync_enabled": true}'
```

### Delete Calendar Integration

```bash
curl -X DELETE http://localhost:8000/api/v1/integrations/calendars/{CALENDAR_ID} \
  -H "Authorization: Bearer YOUR_JWT"
```

## Slack Commands

### Time Capture

In Slack, use:
```
/time 2.5 hours: Client meeting preparation
/time 1.75 hours: Code review
/time 0.5 hours: Email follow-ups
```

Format: `/time [duration] hours: [description]`

### Check Slack Status

```bash
curl http://localhost:8000/api/v1/integrations/slack/status \
  -H "Authorization: Bearer YOUR_JWT" | jq .
```

### Update Slack Preferences

```bash
curl -X PUT http://localhost:8000/api/v1/integrations/slack/preferences \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "daily_summary": true,
    "invoice_notifications": true
  }'
```

### Create Time Entry via Slack API

```bash
curl -X POST http://localhost:8000/api/v1/integrations/slack/time-entry \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "duration_minutes": 150,
    "description": "Client meeting",
    "project_id": "UUID (optional)",
    "client_id": "UUID (optional)"
  }'
```

## Database Queries

### Check OAuth Accounts

```python
from app.db.session import SessionLocal
from app.models.user import UserOAuthAccount

db = SessionLocal()
accounts = db.query(UserOAuthAccount).filter(
    UserOAuthAccount.provider == "google"
).all()
for acc in accounts:
    print(f"{acc.provider}: expires at {acc.expires_at}")
db.close()
```

### Check Calendar Integrations

```python
from app.models.integrations import CalendarIntegration

calendars = db.query(CalendarIntegration).all()
for cal in calendars:
    print(f"{cal.provider}: {cal.calendar_name} (sync={'enabled' if cal.sync_enabled else 'disabled'})")
    print(f"  Last sync: {cal.last_sync_at}")
```

### Check Synced Events

```python
from app.models.integrations import SyncedCalendarEvent

events = db.query(SyncedCalendarEvent).filter(
    SyncedCalendarEvent.calendar_integration_id == calendar_id
).all()
for event in events:
    print(f"{event.event_summary}: {event.event_start} - {event.event_end}")
    if event.time_entry_id:
        print(f"  → Linked to time entry {event.time_entry_id}")
```

### Check Slack Bindings

```python
from app.models.integrations import SlackUserBinding

bindings = db.query(SlackUserBinding).all()
for binding in bindings:
    print(f"{binding.slack_username} ({binding.slack_user_id})")
    print(f"  Daily summary: {binding.notify_daily_summary}")
    print(f"  Invoice notifications: {binding.notify_invoice_ready}")
```

## Background Tasks

### Manually Trigger Sync

```python
from app.services.tasks.integrations import sync_google_calendar
import uuid

calendar_id = uuid.UUID("your-calendar-id")
task = sync_google_calendar.delay(str(calendar_id))
print(f"Task ID: {task.id}")
print(f"Status: {task.status}")
```

### Check Task Status

```python
from app.celery_app import celery_app

task = celery_app.AsyncResult('task-id')
print(f"Status: {task.status}")
print(f"Result: {task.result}")
```

### View Celery Tasks (via Flower)

```bash
# Install Flower if needed
pip install flower

# Run Flower
celery -A app.celery_app flower
# Visit: http://localhost:5555
```

## Testing

### Run Tests

```bash
# All integration tests
pytest tests/integration/test_integrations.py -v

# Specific test
pytest tests/integration/test_integrations.py::TestGoogleCalendarService::test_sync_calendar_events -v

# With coverage
pytest tests/integration/test_integrations.py -v --cov=app.services.integrations
```

### Mock External APIs

Tests use mocks for:
- Google Calendar API
- Microsoft Graph API
- Slack API

No external API calls in tests.

## Troubleshooting

### Token Expired Error

```
"Failed to refresh OAuth token"
```

**Solution:** User needs to re-authenticate
- OAuth account needs refresh token
- Check `UserOAuthAccount.refresh_token` is set
- Run refresh manually: `service.refresh_access_token(oauth_account)`

### Event Not Syncing

**Check:**
1. Calendar `sync_enabled = True`
2. OAuth account exists and has valid token
3. Time window includes the event
4. Event has `dateTime` (not all-day)

**Debug:**
```python
calendar = db.query(CalendarIntegration).get(calendar_id)
print(f"Sync enabled: {calendar.sync_enabled}")
print(f"Last sync: {calendar.last_sync_at}")
print(f"OAuth: {calendar.oauth_account}")
```

### Slack Command Not Working

**Check:**
1. Bot token is valid: `SLACK_BOT_TOKEN`
2. Signing secret is correct: `SLACK_SIGNING_SECRET`
3. Slash command URL is configured in Slack app
4. User is bound: `GET /integrations/slack/status`

**Debug:**
```python
binding = db.query(SlackUserBinding).filter(
    SlackUserBinding.slack_user_id == slack_user_id
).first()
if not binding:
    print("User not bound!")
```

## Documentation

- **Full Guide:** [INTEGRATIONS_IMPLEMENTATION.md](INTEGRATIONS_IMPLEMENTATION.md)
- **Summary:** [INTEGRATIONS_SUMMARY.md](INTEGRATIONS_SUMMARY.md)
- **Code:** `app/services/integrations/`
- **Tests:** `tests/integration/test_integrations.py`

## Key Files

| File | Purpose |
|------|---------|
| `app/services/integrations/google.py` | Google Calendar service |
| `app/services/integrations/outlook.py` | Outlook Calendar service |
| `app/services/integrations/slack_service.py` | Slack service |
| `app/services/tasks/integrations.py` | Celery tasks |
| `app/api/v1/routes/integrations.py` | API endpoints |
| `app/models/integrations.py` | Database models |
| `tests/integration/test_integrations.py` | Tests |

## API Base URL

```
http://localhost:8000/api/v1/integrations
```

All endpoints require `Authorization: Bearer {JWT_TOKEN}` header.

## Support

For issues or questions:
1. Check the full documentation
2. Review test examples
3. Check logs in Celery worker
4. Verify environment variables
