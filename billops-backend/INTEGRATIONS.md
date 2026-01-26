# Integration Implementation Guide

This document describes the OAuth integrations implemented in BillOps:
1. **Google Calendar** - Sync calendar events to time entries
2. **Outlook Calendar** - Sync Outlook calendar to time entries
3. **Slack** - Send notifications and capture time via slash commands

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Google Calendar Integration](#google-calendar-integration)
- [Outlook Calendar Integration](#outlook-calendar-integration)
- [Slack Integration](#slack-integration)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Setup and Configuration](#setup-and-configuration)
- [Scheduled Tasks](#scheduled-tasks)

## Architecture Overview

### Components

1. **Service Layer** (`app/services/integrations/`)
   - `google.py`: GoogleCalendarService for Google Calendar OAuth and sync
   - `outlook.py`: OutlookCalendarService for Outlook Calendar via Microsoft Graph
   - `slack_service.py`: SlackIntegrationService for Slack OAuth and notifications

2. **Models** (`app/models/integrations.py`)
   - CalendarIntegration: Stores calendar provider credentials
   - SyncedCalendarEvent: Tracks calendar events for conversion to time entries
   - SlackIntegration: Workspace-level Slack configuration
   - SlackUserBinding: Links BillOps users to Slack users

3. **API Routes** (`app/api/v1/routes/integrations.py`)
   - OAuth callback handlers
   - Calendar selection and sync endpoints
   - Slack commands and preferences

4. **Celery Tasks** (`app/services/tasks/calendar_sync.py`)
   - Scheduled calendar synchronization
   - Token refresh management

### OAuth Flow Diagram

```
User -> BillOps Frontend
  -> /integrations/{provider}/authorize (get OAuth URL)
  -> User signs in with provider
  -> Redirect to /integrations/{provider}/callback
  -> Backend exchanges code for tokens
  -> Tokens stored in database
```

## Google Calendar Integration

### Overview
Integrates with Google Calendar API to sync events to time entries.

### Service: GoogleCalendarService

Located in `app/services/integrations/google.py`

#### Key Methods

**get_authorization_url()**
- Returns OAuth authorization URL and state for CSRF protection
- Uses offline access to get refresh tokens

```python
auth_url, state = service.get_authorization_url()
```

**handle_callback(auth_code, db)**
- Exchanges authorization code for tokens
- Stores OAuth credentials in UserOAuthAccount
- Returns access_token, refresh_token, expires_at

```python
access_token, refresh_token, expires_at = service.handle_callback(auth_code, db)
```

**refresh_access_token(oauth_account, db)**
- Auto-refreshes expired tokens
- Called before API calls
- Updates oauth_account in database

```python
service.refresh_access_token(oauth_account, db)
```

**get_calendars(access_token)**
- Lists all calendars for the authenticated user
- Returns list of {id, summary}

```python
calendars = service.get_calendars(access_token)
# Output: [{'id': 'primary', 'summary': 'Email@gmail.com'}, ...]
```

**sync_calendar_events(user_id, calendar, oauth_account, db)**
- Fetches events for 7 days in the past and 30 days in the future
- Skips all-day events (only syncs timed events)
- Creates SyncedCalendarEvent records
- Returns sync statistics

```python
result = service.sync_calendar_events(user_id, calendar, oauth_account, db)
# Output: {'status': 'success', 'events_synced': 12, ...}
```

**create_time_entry_from_event(user_id, calendar, event, db)**
- Converts a SyncedCalendarEvent to TimeEntry
- Allows optional project/client assignment
- Returns created TimeEntry

### Configuration

Required environment variables:
```bash
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/integrations/google/callback
```

Obtain from: https://console.cloud.google.com/

### API Endpoints

```
GET  /api/v1/integrations/google/authorize
POST /api/v1/integrations/google/callback
POST /api/v1/integrations/google/select-calendar
POST /api/v1/integrations/google/{calendar_id}/sync
```

## Outlook Calendar Integration

### Overview
Integrates with Microsoft Graph API to sync Outlook calendar events to time entries.

### Service: OutlookCalendarService

Located in `app/services/integrations/outlook.py`

#### Key Methods

**get_authorization_url()**
- Returns Microsoft OAuth authorization URL
- Uses Microsoft Graph API scopes

```python
auth_url, state = service.get_authorization_url()
```

**handle_callback(auth_code)**
- Exchanges authorization code for Microsoft tokens
- Returns access_token, refresh_token, expires_at

```python
access_token, refresh_token, expires_at = service.handle_callback(auth_code)
```

**refresh_access_token(oauth_account, db)**
- Refreshes expired Microsoft tokens
- Updates oauth_account in database

```python
service.refresh_access_token(oauth_account, db)
```

**get_calendars(access_token)**
- Lists Outlook calendars via Microsoft Graph /me/calendars
- Returns list of {id, name}

```python
calendars = service.get_calendars(access_token)
# Output: [{'id': 'calendar-id-123', 'name': 'Calendar'}, ...]
```

**sync_calendar_events(user_id, calendar, oauth_account, db)**
- Fetches dateTime events (excludes all-day)
- Queries Microsoft Graph /me/calendars/{id}/events
- Handles ISO 8601 date format with timezone
- Creates SyncedCalendarEvent records

```python
result = service.sync_calendar_events(user_id, calendar, oauth_account, db)
```

### Configuration

Required environment variables:
```bash
MICROSOFT_CLIENT_ID=<your-client-id>
MICROSOFT_CLIENT_SECRET=<your-client-secret>
MICROSOFT_TENANT_ID=<tenant-id>  # e.g., "common" or your tenant ID
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/integrations/microsoft/callback
```

Obtain from: https://portal.azure.com/

### API Endpoints

```
GET  /api/v1/integrations/microsoft/authorize
POST /api/v1/integrations/microsoft/callback
POST /api/v1/integrations/microsoft/select-calendar
POST /api/v1/integrations/microsoft/{calendar_id}/sync
```

## Slack Integration

### Overview
Integrates Slack workspace for:
- Sending notifications (time entries, invoices, daily summaries)
- Slash commands for time capture (/time)
- User binding and preference management

### Service: SlackIntegrationService

Located in `app/services/integrations/slack_service.py`

#### Key Methods

**get_authorization_url()**
- Returns Slack OAuth authorization URL
- Scopes: chat:write, commands, users:read, users:read.email

```python
auth_url = service.get_authorization_url()
```

**handle_oauth_callback(auth_code)**
- Exchanges authorization code for bot token
- Returns workspace_id, bot_token, app_id, workspace_name

```python
result = service.handle_oauth_callback(auth_code)
# Output: {
#   'status': 'success',
#   'workspace_id': 'T12345678',
#   'bot_token': 'xoxb-...',
#   'app_id': 'A12345678',
#   'workspace_name': 'My Workspace'
# }
```

**verify_slack_request(request_body, x_slack_signature, x_request_timestamp)**
- Verifies webhook signature (HMAC-SHA256)
- Checks timestamp is within 5 minutes
- Required for all webhook requests

```python
is_valid = service.verify_slack_request(body, signature, timestamp)
```

**send_message(channel, text, blocks=None, thread_ts=None)**
- Posts message to Slack channel
- Supports Block Kit formatting

```python
service.send_message('C12345678', 'Hello World')
```

**send_notification(user_id, title, message, notification_type='info')**
- Sends DM to Slack user with color-coded block
- Types: 'info' (blue), 'success' (green), 'warning' (yellow), 'error' (red)

```python
service.send_notification(user_id, 'Time Entry', 'Logged 2.5 hours', 'success')
```

**notify_time_entry_created(time_entry, user)**
- Notifies user when time entry created
- Shows project, duration, client

```python
service.notify_time_entry_created(time_entry, user)
# Message: ⏱️ Time entry logged: 2.5 hours for Project Name
```

**notify_invoice_ready(invoice_number, total_cents, user_id)**
- Notifies user when invoice is ready
- Shows invoice number and total

```python
service.notify_invoice_ready('INV-001', 150000, 'U12345678')
# Message: 📄 Invoice INV-001 ready: $1,500.00
```

**send_daily_summary(user_id, total_hours, entry_count)**
- Sends daily summary with total hours and entries

```python
service.send_daily_summary('U12345678', 8.5, 5)
# Message: 📊 Daily Summary: 5 entries logged (8.5 hours)
```

**handle_time_capture_command(slack_user_id, command_text)**
- Parses /time command
- Format: "/time 2.5 hours: Meeting with client"
- Creates backdated TimeEntry

```python
result = service.handle_time_capture_command('U12345678', '2.5 hours: Meeting')
# Output: {
#   'status': 'success',
#   'message': 'Time entry created: 2.5 hours',
#   'time_entry_id': '...'
# }
```

**list_workspace_users()**
- Returns all users in Slack workspace

```python
users = service.list_workspace_users()
# Output: [{'id': 'U12345678', 'name': 'john.doe', 'profile': {...}}, ...]
```

### Configuration

Required environment variables:
```bash
SLACK_BOT_TOKEN=xoxb-...  # For workspace already installed
SLACK_SIGNING_SECRET=...
SLACK_APP_ID=A...
SLACK_CLIENT_ID=...
SLACK_CLIENT_SECRET=...
SLACK_REDIRECT_URI=http://localhost:8000/api/v1/integrations/slack/callback
```

Obtain from: https://api.slack.com/apps

### Slack App Setup

1. Create app at https://api.slack.com/apps
2. Enable Slash Commands
   - Command: `/time`
   - Request URL: `https://your-domain/api/v1/integrations/slack/commands/time`
3. Enable Bot User Scopes
   - chat:write
   - commands
   - users:read
   - users:read.email
4. Set OAuth Redirect URL
   - `https://your-domain/api/v1/integrations/slack/callback`

### API Endpoints

```
GET  /api/v1/integrations/slack/authorize
POST /api/v1/integrations/slack/callback
POST /api/v1/integrations/slack/commands/time
GET  /api/v1/integrations/slack/status
PUT  /api/v1/integrations/slack/preferences
```

## Database Schema

### CalendarIntegration
- Stores calendar provider configuration
- Links user to OAuth account
- Tracks sync status and schedule

Fields:
- `id`: UUID primary key
- `user_id`: Reference to User
- `oauth_account_id`: Reference to UserOAuthAccount
- `provider`: 'google' or 'microsoft'
- `provider_calendar_id`: ID of calendar on provider
- `calendar_name`: Display name
- `is_active`: Whether integration is active
- `sync_enabled`: Whether auto-sync is enabled
- `last_synced_at`: Timestamp of last sync

### SyncedCalendarEvent
- Stores calendar events synced from provider
- Can be converted to TimeEntry manually

Fields:
- `id`: UUID primary key
- `calendar_id`: Reference to CalendarIntegration
- `user_id`: Reference to User
- `time_entry_id`: Optional reference to created TimeEntry
- `provider_event_id`: ID of event on provider (for deduplication)
- `event_title`: Event name
- `event_description`: Event description
- `event_start`: Event start datetime
- `event_end`: Event end datetime
- `is_synced`: Whether converted to TimeEntry

### SlackIntegration
- Stores workspace-level Slack configuration

Fields:
- `id`: UUID primary key
- `workspace_id`: Slack workspace ID
- `workspace_name`: Slack workspace name
- `bot_token`: OAuth token for bot
- `app_id`: Slack app ID
- `is_active`: Whether integration is active
- `notifications_enabled`: Send notifications
- `time_capture_enabled`: /time command enabled

### SlackUserBinding
- Links BillOps user to Slack user
- Controls notification preferences

Fields:
- `id`: UUID primary key
- `user_id`: Reference to User
- `slack_integration_id`: Reference to SlackIntegration
- `slack_user_id`: Slack user ID
- `slack_username`: Slack username
- `slack_email`: Slack email
- `notify_time_entry_created`: Send time entry notifications
- `notify_invoice_ready`: Send invoice notifications
- `notify_daily_summary`: Send daily summaries

## API Endpoints

### Google Calendar

**GET /api/v1/integrations/google/authorize**
Get OAuth authorization URL for Google Calendar.

Response:
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "random-state-string"
}
```

**POST /api/v1/integrations/google/callback**
Handle OAuth callback with authorization code.

Request:
```json
{
  "code": "authorization-code-from-google"
}
```

Response:
```json
{
  "status": "success",
  "calendars": [
    {"id": "primary", "summary": "user@gmail.com"},
    {"id": "cal-id", "summary": "Work"}
  ],
  "access_token": "...",
  "refresh_token": "..."
}
```

**POST /api/v1/integrations/google/select-calendar**
Select a calendar to sync.

Request:
```json
{
  "calendar_id": "primary",
  "calendar_name": "user@gmail.com",
  "access_token": "..."
}
```

Response:
```json
{
  "status": "success",
  "calendar_id": "uuid",
  "message": "Calendar 'user@gmail.com' selected"
}
```

**POST /api/v1/integrations/google/{calendar_id}/sync**
Sync events from Google Calendar.

Response:
```json
{
  "status": "success",
  "events_synced": 12,
  "new_events": 5,
  "updated_events": 3
}
```

### Microsoft/Outlook Calendar

**GET /api/v1/integrations/microsoft/authorize**
Get OAuth authorization URL for Microsoft.

**POST /api/v1/integrations/microsoft/callback**
Handle Microsoft OAuth callback.

**POST /api/v1/integrations/microsoft/select-calendar**
Select Outlook calendar to sync.

**POST /api/v1/integrations/microsoft/{calendar_id}/sync**
Sync events from Outlook Calendar.

### Slack

**GET /api/v1/integrations/slack/authorize**
Get Slack OAuth authorization URL.

Response:
```json
{
  "auth_url": "https://slack.com/oauth/v2/authorize?..."
}
```

**POST /api/v1/integrations/slack/callback**
Handle Slack OAuth callback.

Request:
```json
{
  "code": "authorization-code-from-slack"
}
```

Response:
```json
{
  "status": "success",
  "workspace_id": "T12345678",
  "workspace_name": "My Workspace",
  "message": "Slack workspace integrated successfully"
}
```

**POST /api/v1/integrations/slack/commands/time**
Handle /time slash command.

Request (from Slack):
```
/time 2.5 hours: Meeting with client
```

Response (to Slack):
```json
{
  "status": "success",
  "message": "Time entry created: 2.5 hours"
}
```

**GET /api/v1/integrations/slack/status**
Get Slack integration status for current user.

Response:
```json
{
  "status": "connected",
  "slack_user_id": "U12345678",
  "slack_username": "john.doe",
  "daily_summary_enabled": true,
  "invoice_notifications_enabled": true
}
```

**PUT /api/v1/integrations/slack/preferences**
Update Slack notification preferences.

Request:
```json
{
  "daily_summary": true,
  "invoice_notifications": true
}
```

## Setup and Configuration

### 1. Environment Variables

Create `.env` file with:

```bash
# Google Calendar
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/integrations/google/callback

# Microsoft/Outlook
MICROSOFT_CLIENT_ID=<your-client-id>
MICROSOFT_CLIENT_SECRET=<your-client-secret>
MICROSOFT_TENANT_ID=common
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/integrations/microsoft/callback

# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_ID=A...
SLACK_CLIENT_ID=...
SLACK_CLIENT_SECRET=...
SLACK_REDIRECT_URI=http://localhost:8000/api/v1/integrations/slack/callback

# Frontend
FRONTEND_URL=http://localhost:3000
```

### 2. Google Cloud Console Setup

1. Go to https://console.cloud.google.com/
2. Create OAuth 2.0 credentials (OAuth client ID)
3. Set Authorized Redirect URIs
4. Download client credentials
5. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET

### 3. Azure/Microsoft Setup

1. Go to https://portal.azure.com/
2. Register application in Azure AD
3. Create client secret
4. Set Redirect URI
5. Grant API permissions for Microsoft Graph

### 4. Slack App Setup

1. Go to https://api.slack.com/apps
2. Create New App
3. Set OAuth Redirect URLs
4. Create Slash Command
5. Request Bot User OAuth Scopes:
   - chat:write
   - commands
   - users:read
   - users:read.email
6. Install to workspace
7. Copy bot token and signing secret

### 5. Database Migrations

```bash
cd billops-backend
alembic upgrade head
```

This will create:
- calendar_integrations table
- synced_calendar_events table
- slack_integrations table
- slack_user_bindings table

## Scheduled Tasks

### Calendar Sync (Celery)

Located in `app/services/tasks/calendar_sync.py`

**sync_all_calendars**
- Runs periodically (default: every 60 minutes)
- Syncs all active calendars with sync_enabled=true
- Calls provider-specific sync logic

```python
celery_app.conf.beat_schedule = {
    'sync-all-calendars': {
        'task': 'calendar:sync_all',
        'schedule': crontab(minute=0),  # Every hour
    },
}
```

**sync_single_calendar(calendar_id)**
- Syncs a specific calendar on demand
- Used by API endpoint for immediate sync

**refresh_all_tokens**
- Runs periodically (default: every 12 hours)
- Refreshes all expired OAuth tokens
- Prevents token expiration errors

```python
celery_app.conf.beat_schedule = {
    'refresh-oauth-tokens': {
        'task': 'calendar:refresh_tokens',
        'schedule': crontab(hour='*/12'),  # Every 12 hours
    },
}
```

### Configuration

Edit `app/workers/celeryconfig.py` to adjust schedule:

```python
from celery.schedules import crontab

beat_schedule = {
    'sync-all-calendars': {
        'task': 'calendar:sync_all',
        'schedule': crontab(minute=0),  # Every hour
    },
    'refresh-oauth-tokens': {
        'task': 'calendar:refresh_tokens',
        'schedule': crontab(hour='*/12'),  # Every 12 hours
    },
}
```

## Testing

### Unit Tests

```python
from app.services.integrations.google import GoogleCalendarService

def test_get_authorization_url():
    service = GoogleCalendarService()
    auth_url, state = service.get_authorization_url()
    assert auth_url.startswith('https://accounts.google.com/')
    assert state is not None
```

### Integration Tests

Test with real OAuth providers:

```bash
# Start server
python -m uvicorn app.main:app --reload

# Test Google Calendar
curl http://localhost:8000/api/v1/integrations/google/authorize

# Test Slack
curl http://localhost:8000/api/v1/integrations/slack/authorize
```

## Error Handling

### Common Errors

**Invalid redirect URI**
- Ensure REDIRECT_URI matches provider configuration
- Check environment variables are set correctly

**Token expired**
- refresh_access_token() handles auto-refresh
- Celery task runs every 12 hours to refresh tokens

**Slack verification failed**
- Ensure SLACK_SIGNING_SECRET is correct
- Check timestamp is within 5 minutes

**Calendar not found**
- Verify calendar_id exists
- Check user has permission to access calendar

## Best Practices

1. **Security**
   - Store tokens securely in database (encrypted in production)
   - Use HTTPS for all OAuth redirects
   - Validate CSRF tokens (state parameter)
   - Verify Slack webhook signatures

2. **Performance**
   - Use Celery for scheduled tasks
   - Cache calendar lists (TTL: 1 hour)
   - Batch event syncs
   - Index provider_event_id for deduplication

3. **User Experience**
   - Show synced events before conversion
   - Allow user to select/edit before creating TimeEntry
   - Provide clear error messages
   - Send Slack notifications for important events

4. **Monitoring**
   - Log all OAuth callbacks
   - Track sync statistics
   - Monitor Slack API errors
   - Set up alerts for token refresh failures
