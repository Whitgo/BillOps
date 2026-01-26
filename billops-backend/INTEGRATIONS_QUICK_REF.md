# Integration Quick Reference

## Environment Variables Required

```bash
# Google Calendar OAuth
GOOGLE_CLIENT_ID=<client-id>
GOOGLE_CLIENT_SECRET=<client-secret>
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/integrations/google/callback

# Microsoft/Outlook OAuth
MICROSOFT_CLIENT_ID=<client-id>
MICROSOFT_CLIENT_SECRET=<client-secret>
MICROSOFT_TENANT_ID=common
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/integrations/microsoft/callback

# Slack OAuth
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_ID=A...
SLACK_CLIENT_ID=...
SLACK_CLIENT_SECRET=...
SLACK_REDIRECT_URI=http://localhost:8000/api/v1/integrations/slack/callback

# Frontend
FRONTEND_URL=http://localhost:3000
```

## API Endpoints Summary

### Google Calendar
```
GET  /api/v1/integrations/google/authorize          # Get OAuth URL
POST /api/v1/integrations/google/callback           # OAuth callback
POST /api/v1/integrations/google/select-calendar    # Select calendar
POST /api/v1/integrations/google/{id}/sync          # Sync events
```

### Outlook Calendar
```
GET  /api/v1/integrations/microsoft/authorize
POST /api/v1/integrations/microsoft/callback
POST /api/v1/integrations/microsoft/select-calendar
POST /api/v1/integrations/microsoft/{id}/sync
```

### Slack
```
GET  /api/v1/integrations/slack/authorize           # Get OAuth URL
POST /api/v1/integrations/slack/callback            # OAuth callback
POST /api/v1/integrations/slack/commands/time       # /time command
GET  /api/v1/integrations/slack/status              # Check binding
PUT  /api/v1/integrations/slack/preferences         # Update prefs
```

## Database Models

### CalendarIntegration
Store per-calendar configuration (one per provider per user)
- Fields: id, user_id, oauth_account_id, provider, calendar_id, calendar_name, is_active, sync_enabled

### SyncedCalendarEvent
Store synced calendar events (can be converted to TimeEntry)
- Fields: id, calendar_id, provider_event_id, event_title, event_start, event_end, is_synced

### SlackIntegration
Store workspace-level Slack config (one per workspace)
- Fields: id, workspace_id, bot_token, app_id, is_active

### SlackUserBinding
Link BillOps user to Slack user (optional per user)
- Fields: id, user_id, slack_user_id, notification preferences

## OAuth Flow (All Providers)

1. Frontend calls `GET /api/v1/integrations/{provider}/authorize`
2. Backend returns auth_url → User signs in with provider
3. Provider redirects to `POST /api/v1/integrations/{provider}/callback?code=...`
4. Backend exchanges code for access_token/refresh_token
5. Tokens stored in UserOAuthAccount → Integration ready

## Service Usage Examples

### Google Calendar
```python
from app.services.integrations.google import GoogleCalendarService

service = GoogleCalendarService()

# 1. Get authorization URL
auth_url, state = service.get_authorization_url()

# 2. Handle callback
access_token, refresh_token, expires_at = service.handle_callback(code, db)

# 3. Get calendars
calendars = service.get_calendars(access_token)

# 4. Sync events
result = service.sync_calendar_events(user_id, calendar, oauth_account, db)

# 5. Refresh token (auto-called)
service.refresh_access_token(oauth_account, db)
```

### Outlook Calendar
```python
from app.services.integrations.outlook import OutlookCalendarService

service = OutlookCalendarService()

# 1. Get authorization URL
auth_url, state = service.get_authorization_url()

# 2. Handle callback
access_token, refresh_token, expires_at = service.handle_callback(code)

# 3. Get calendars (Microsoft Graph API)
calendars = service.get_calendars(access_token)

# 4. Sync events
result = service.sync_calendar_events(user_id, calendar, oauth_account, db)
```

### Slack
```python
from app.services.integrations.slack_service import SlackIntegrationService

service = SlackIntegrationService(bot_token='xoxb-...')

# 1. Get authorization URL (for workspace installation)
auth_url = service.get_authorization_url()

# 2. Handle callback
result = service.handle_oauth_callback(code)

# 3. Send notification
service.send_notification(user_id, 'Title', 'Message', 'success')

# 4. Handle time capture command
result = service.handle_time_capture_command(slack_user_id, '2.5 hours: Meeting')

# 5. Verify webhook
is_valid = service.verify_slack_request(body, signature, timestamp)
```

## Celery Tasks

```bash
# Run all scheduled syncs
celery -A app.celery_app worker -B

# Manually trigger calendar sync
celery -A app.celery_app call calendar:sync_all

# Trigger single calendar sync
celery -A app.celery_app call calendar:sync_single --args='["calendar-uuid"]'

# Refresh all tokens
celery -A app.celery_app call calendar:refresh_tokens
```

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Invalid redirect URI | URI mismatch | Check env var matches provider config |
| Token expired | Not refreshing | Task runs every 12h, or call refresh manually |
| Slack signature invalid | Wrong secret | Verify SLACK_SIGNING_SECRET |
| Calendar not found | Bad calendar_id | Use /authorize endpoint to list |
| OAuth callback fails | Code expired | Use code within minutes of generation |
| Permissions error | Missing scopes | Check OAuth scopes in provider config |

## File Structure

```
billops-backend/
├── app/
│   ├── api/v1/routes/
│   │   └── integrations.py          ← API endpoints
│   ├── models/
│   │   └── integrations.py          ← Database models
│   ├── services/
│   │   ├── integrations/
│   │   │   ├── google.py            ← Google Calendar service
│   │   │   ├── outlook.py           ← Outlook service
│   │   │   └── slack_service.py     ← Slack service
│   │   └── tasks/
│   │       └── calendar_sync.py     ← Celery tasks
│   └── config/
│       └── settings.py              ← OAuth configuration
├── migrations/versions/
│   └── 4a8c9b1d2e3f_add_calendar... ← Database schema
├── requirements.txt                 ← Dependencies
└── INTEGRATIONS.md                  ← Full documentation
```

## Testing Checklist

- [ ] Google Calendar OAuth flow works
- [ ] Outlook Calendar OAuth flow works
- [ ] Slack workspace installation works
- [ ] Calendar events sync correctly
- [ ] Time entry created from synced event
- [ ] Slack notifications sent
- [ ] /time command captures time
- [ ] Token refresh works
- [ ] Daily summaries sent on schedule
