# Integration Guide: Google Calendar, Outlook, and Slack

This guide covers the implementation and usage of Google Calendar, Outlook Calendar (Microsoft Graph), and Slack integrations in BillOps.

## Table of Contents
1. [Google Calendar Integration](#google-calendar-integration)
2. [Outlook Calendar Integration](#outlook-calendar-integration)
3. [Slack Integration](#slack-integration)
4. [Event Synchronization](#event-synchronization)
5. [Configuration](#configuration)
6. [API Endpoints](#api-endpoints)
7. [Background Tasks](#background-tasks)

## Google Calendar Integration

### OAuth Flow

The Google Calendar integration uses OAuth 2.0 to securely access a user's calendar.

#### Setup Steps

1. **Create OAuth 2.0 Credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select an existing one
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials (Web application)
   - Configure authorized redirect URIs: `https://yourdomain.com/api/v1/integrations/google/callback`

2. **Add to BillOps Configuration**
   ```
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   GOOGLE_REDIRECT_URI=https://yourdomain.com/api/v1/integrations/google/callback
   ```

#### OAuth Flow Process

1. User clicks "Connect Google Calendar"
2. Frontend gets authorization URL from `/api/v1/integrations/google/authorize`
3. User is redirected to Google login and grants permission
4. Google redirects to callback with authorization code
5. Backend exchanges code for access and refresh tokens
6. Tokens are stored in `UserOAuthAccount` table
7. User selects which calendar to sync
8. Sync starts with `/api/v1/integrations/google/{calendar_id}/sync`

#### Implementation Details

**Service: `GoogleCalendarService`**

Key methods:
- `get_auth_flow()` - Creates OAuth flow
- `get_authorization_url()` - Returns auth URL and state
- `handle_callback(auth_code, db)` - Exchanges code for tokens
- `store_oauth_credentials()` - Saves OAuth account
- `refresh_access_token()` - Refreshes expired tokens
- `get_calendars()` - Lists user's calendars
- `sync_calendar_events()` - Syncs events from calendar
- `create_time_entry_from_event()` - Converts event to time entry

**Scopes:**
- `https://www.googleapis.com/auth/calendar` - Read/write access

### Event Sync

Events are synced within a configurable time window (default: 7 days back, 30 days forward).

**Features:**
- Only syncs timed events (skips all-day events)
- Prevents duplicate syncs (checks by provider event ID)
- Creates `SyncedCalendarEvent` records
- Can convert events to billable time entries
- Tracks last sync timestamp

## Outlook Calendar Integration

### OAuth Flow

Uses Microsoft Graph API for OAuth 2.0 and calendar access.

#### Setup Steps

1. **Create Azure App Registration**
   - Go to [Azure Portal](https://portal.azure.com)
   - Navigate to Azure Active Directory > App registrations
   - Create new app registration
   - Under Certificates & secrets, create a client secret
   - Add API permissions:
     - `Calendars.Read`
     - `Calendars.ReadWrite`
   - Configure redirect URIs: `https://yourdomain.com/api/v1/integrations/microsoft/callback`

2. **Add to BillOps Configuration**
   ```
   MICROSOFT_CLIENT_ID=your_client_id
   MICROSOFT_CLIENT_SECRET=your_client_secret
   MICROSOFT_TENANT_ID=your_tenant_id
   MICROSOFT_REDIRECT_URI=https://yourdomain.com/api/v1/integrations/microsoft/callback
   ```

#### OAuth Flow Process

Similar to Google Calendar:
1. User clicks "Connect Outlook Calendar"
2. Frontend gets authorization URL from `/api/v1/integrations/microsoft/authorize`
3. User authenticates with Microsoft account
4. Access and refresh tokens are stored
5. User selects calendar to sync
6. Sync starts with `/api/v1/integrations/microsoft/{calendar_id}/sync`

#### Implementation Details

**Service: `OutlookCalendarService`**

Key methods:
- `get_authorization_url()` - Returns auth URL and state
- `handle_callback(auth_code)` - Exchanges code for tokens
- `store_oauth_credentials()` - Saves OAuth account
- `refresh_access_token()` - Refreshes expired tokens
- `get_calendars()` - Lists user's calendars via Microsoft Graph
- `sync_calendar_events()` - Syncs events from calendar
- `create_time_entry_from_event()` - Converts event to time entry

**API Endpoint:** `https://graph.microsoft.com/v1.0`

### Event Sync

Same features as Google Calendar but uses Microsoft Graph API events format.

## Slack Integration

### OAuth Installation

Slack integration uses OAuth 2.0 for workspace authorization.

#### Setup Steps

1. **Create Slack App**
   - Go to [Slack App Directory](https://api.slack.com/apps)
   - Create new app
   - Set basic information (name, icon)
   - Navigate to OAuth & Permissions
   - Add scopes:
     - `chat:write` - Send messages
     - `commands` - Listen to commands
     - `users:read` - Read user info
     - `users:read.email` - Read user emails
     - `app_mentions:read` - Listen to mentions
   - Set redirect URL: `https://yourdomain.com/api/v1/integrations/slack/callback`

2. **Add to BillOps Configuration**
   ```
   SLACK_CLIENT_ID=your_client_id
   SLACK_CLIENT_SECRET=your_client_secret
   SLACK_REDIRECT_URI=https://yourdomain.com/api/v1/integrations/slack/callback
   SLACK_BOT_TOKEN=xoxb-your-token (from workspace installation)
   SLACK_SIGNING_SECRET=your_signing_secret
   SLACK_APP_ID=your_app_id
   ```

3. **Configure Slash Commands** (in Slack App Settings)
   - Command: `/time`
   - Request URL: `https://yourdomain.com/api/v1/integrations/slack/commands/time`
   - Short description: "Log work hours"
   - Usage hint: `[duration] hours: [description]`

#### Workspace Installation

1. Admin goes to `/api/v1/integrations/slack/authorize`
2. Authorizes app in Slack workspace
3. App receives bot token and workspace info
4. Stores in `SlackIntegration` table

#### User Linking

Each Slack user must link their Slack account to their BillOps account:
1. User authenticates with Slack (via Slack app)
2. Maps to BillOps user via `/api/v1/integrations/slack/callback`
3. Creates `SlackUserBinding` record
4. Can now receive notifications and use commands

### Notifications

**Types of Notifications:**

1. **Time Entry Created**
   - Triggered when time entry is created
   - Includes: description, duration, date
   - Sent via DM to user

2. **Invoice Ready**
   - Triggered when invoice is finalized
   - Includes: invoice number, total amount
   - Sent via DM to user

3. **Daily Summary**
   - Scheduled task (e.g., 5 PM daily)
   - Shows: entry count, total hours
   - User can enable/disable preference

### Slash Commands

**Time Capture Command:**
```
/time 2.5 hours: Client meeting preparation
```

Returns: Confirmation message in channel

**Implementation:**
- Parses duration and description
- Creates time entry backdated to specified duration
- Sends confirmation
- Triggers notification if enabled

### Time Capture Events

When a time entry is created via Slack:
1. Command is parsed
2. `TimeEntry` is created with source="slack"
3. Notification is sent to user
4. Entry is visible in web UI

### Implementation Details

**Service: `SlackIntegrationService`**

Key methods:
- `verify_slack_request()` - Verifies request signature
- `get_authorization_url()` - Returns OAuth URL
- `handle_oauth_callback()` - Exchanges code for bot token
- `send_message()` - Sends message to channel
- `send_notification()` - Sends DM notification
- `notify_time_entry_created()` - Notifies time entry creation
- `notify_invoice_ready()` - Notifies invoice is ready
- `send_daily_summary()` - Sends daily summary
- `handle_time_capture_command()` - Processes /time command
- `list_workspace_users()` - Gets workspace members

## Event Synchronization

### Sync Process

1. **Trigger**
   - Manual: POST `/api/v1/integrations/{provider}/{calendar_id}/sync`
   - Automatic: Celery task runs at configured interval (default: every hour)

2. **Steps**
   - Fetch calendar from database
   - Refresh OAuth token if expired
   - Query calendar API for events in time window
   - For each event:
     - Check if already synced (by provider event ID)
     - Create or update `SyncedCalendarEvent`
   - Update calendar's `last_sync_at` timestamp

3. **Conversion to Time Entry**
   - User selects synced event from list
   - POST `/api/v1/integrations/calendars/events/convert`
   - Event is converted to `TimeEntry` with:
     - Start/end times from calendar event
     - Duration calculated from times
     - Description from event title
     - Status: "pending" (requires approval)
   - Event marked as `is_synced = True`

### Sync Configuration

Each `CalendarIntegration` has:
- `sync_enabled` - Whether syncing is active
- `sync_interval_minutes` - How often to sync (default: 60)
- `sync_config` - JSON with additional settings
- `last_sync_at` - Timestamp of last sync

## Configuration

### Environment Variables

**Google Calendar:**
```
GOOGLE_CLIENT_ID=abc123.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xyz
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/integrations/google/callback
```

**Outlook Calendar:**
```
MICROSOFT_CLIENT_ID=00000000-0000-0000-0000-000000000000
MICROSOFT_CLIENT_SECRET=abc~xyz
MICROSOFT_TENANT_ID=common
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/integrations/microsoft/callback
```

**Slack:**
```
SLACK_CLIENT_ID=000000000000.000000000000
SLACK_CLIENT_SECRET=abc123def456
SLACK_REDIRECT_URI=http://localhost:8000/api/v1/integrations/slack/callback
SLACK_BOT_TOKEN=xoxb-000000000000-000000000000-abc123def456
SLACK_SIGNING_SECRET=abc123def456
SLACK_APP_ID=A00000000000
```

## API Endpoints

### Google Calendar

- `GET /integrations/google/authorize` - Get authorization URL
- `POST /integrations/google/callback` - Handle OAuth callback
- `POST /integrations/google/select-calendar` - Select calendar to sync
- `POST /integrations/google/{calendar_id}/sync` - Manual sync

### Outlook Calendar

- `GET /integrations/microsoft/authorize` - Get authorization URL
- `POST /integrations/microsoft/callback` - Handle OAuth callback
- `POST /integrations/microsoft/select-calendar` - Select calendar to sync
- `POST /integrations/microsoft/{calendar_id}/sync` - Manual sync

### Slack

- `GET /integrations/slack/authorize` - Get authorization URL
- `POST /integrations/slack/callback` - Handle OAuth callback
- `POST /integrations/slack/commands/time` - Handle slash command
- `GET /integrations/slack/status` - Get current user's Slack status
- `PUT /integrations/slack/preferences` - Update notification preferences

### Calendar Management (All Providers)

- `GET /integrations/calendars` - List all integrated calendars
- `PUT /integrations/calendars/{calendar_id}/enable` - Enable/disable sync
- `DELETE /integrations/calendars/{calendar_id}` - Delete calendar
- `GET /integrations/calendars/{calendar_id}/events` - List synced events
- `POST /integrations/calendars/events/convert` - Convert event to time entry

### Slack Time Capture

- `POST /integrations/slack/time-entry` - Create time entry via API
- Slash command: `/time 2.5 hours: Description`

## Background Tasks

### Celery Tasks

All tasks are located in `app/services/tasks/integrations.py`

**Sync Tasks:**

1. `sync_google_calendar(calendar_integration_id)`
   - Syncs single Google Calendar
   - Scheduled per calendar's `sync_interval_minutes`
   - Max 3 retries with exponential backoff

2. `sync_outlook_calendar(calendar_integration_id)`
   - Syncs single Outlook Calendar
   - Scheduled per calendar's `sync_interval_minutes`
   - Max 3 retries with exponential backoff

3. `sync_all_calendars()`
   - Finds all active, enabled calendars
   - Schedules individual sync tasks
   - Called hourly (configurable)

**Notification Tasks:**

1. `send_slack_daily_summaries()`
   - Sends daily summaries to all Slack-bound users
   - Scheduled daily (configurable time)
   - Includes: entry count, total hours

2. `send_invoice_notifications(invoice_id)`
   - Sends notification when invoice is ready
   - Called when invoice status changes to "ready"
   - Respects user notification preferences

### Beat Scheduler

Configure in `app/workers/celeryconfig.py`:

```python
app.conf.beat_schedule = {
    'sync-all-calendars': {
        'task': 'app.services.tasks.integrations.sync_all_calendars',
        'schedule': crontab(minute=0),  # Every hour
    },
    'send-slack-summaries': {
        'task': 'app.services.tasks.integrations.send_slack_daily_summaries',
        'schedule': crontab(hour=17, minute=0),  # 5 PM daily
    },
}
```

## Error Handling

### OAuth Token Expiration

- Services automatically refresh expired tokens
- If refresh fails, sync is skipped with error
- User is notified to re-authenticate

### API Rate Limiting

- Implement exponential backoff for retries
- Cache calendar lists for reasonable duration
- Batch requests where possible

### Sync Failures

- Tasks retry up to 3 times with exponential backoff
- Failures are logged with full context
- Last known state is preserved

## Security Considerations

1. **OAuth Tokens**
   - Never expose to frontend
   - Store refresh tokens securely
   - Implement token rotation

2. **Slack Request Verification**
   - All Slack requests are signature-verified
   - Timestamp must be within 5 minutes
   - Signing secret must be configured

3. **User Binding**
   - Only allow users to access their own integrations
   - Verify user_id in all requests
   - Scope calendar events to authenticated user

4. **Rate Limiting**
   - Implement rate limits on OAuth endpoints
   - Use exponential backoff for retries
   - Cache results appropriately

## Testing

### Manual Testing

1. **Google Calendar**
   ```bash
   # Get auth URL
   curl http://localhost:8000/api/v1/integrations/google/authorize
   
   # Visit returned auth_url, then callback with code
   curl -X POST http://localhost:8000/api/v1/integrations/google/callback \
     -H "Authorization: Bearer YOUR_JWT" \
     -H "Content-Type: application/json" \
     -d '{"code": "auth_code"}'
   
   # Select calendar
   curl -X POST http://localhost:8000/api/v1/integrations/google/select-calendar \
     -H "Authorization: Bearer YOUR_JWT" \
     -H "Content-Type: application/json" \
     -d '{"calendar_id": "...", "calendar_name": "...", "oauth_account_id": "..."}'
   
   # Manual sync
   curl -X POST http://localhost:8000/api/v1/integrations/google/{calendar_id}/sync \
     -H "Authorization: Bearer YOUR_JWT"
   ```

2. **Slack**
   ```bash
   # Get auth URL
   curl http://localhost:8000/api/v1/integrations/slack/authorize
   
   # Simulate slash command (in real usage, sent by Slack)
   curl -X POST http://localhost:8000/api/v1/integrations/slack/commands/time \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "user_id=U123&text=2%20hours:%20Meeting"
   ```

### Unit Tests

Tests are located in `tests/integration/test_*.py`

```bash
# Run integration tests
python -m pytest tests/integration/ -v

# Run specific test
python -m pytest tests/integration/test_google_calendar.py -v
```

### Integration Tests

Full workflow tests including:
- OAuth flow completion
- Calendar sync
- Event conversion
- Slack notifications
