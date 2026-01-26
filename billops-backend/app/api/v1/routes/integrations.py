"""Integration routes for calendar OAuth and Slack."""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.v1.dependencies import get_current_user, get_db
from app.models.user import User, UserOAuthAccount
from app.models.integrations import CalendarIntegration, SlackIntegration, SlackUserBinding, SyncedCalendarEvent
from app.models.time_entry import TimeEntry
from app.services.integrations.google import GoogleCalendarService
from app.services.integrations.outlook import OutlookCalendarService
from app.services.integrations.slack_service import SlackIntegrationService

router = APIRouter(prefix="/integrations", tags=["integrations"])


# ===== Google Calendar Routes =====

class GoogleAuthRequest(BaseModel):
    code: str


class GoogleCalendarSelectRequest(BaseModel):
    calendar_id: str
    calendar_name: str


@router.get("/google/authorize")
async def google_authorize():
    """Get Google OAuth authorization URL."""
    try:
        service = GoogleCalendarService()
        auth_url, state = service.get_authorization_url()
        return {
            "auth_url": auth_url,
            "state": state
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/google/callback")
async def google_callback(
    request: GoogleAuthRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Handle Google OAuth callback and store credentials."""
    try:
        service = GoogleCalendarService()
        access_token, refresh_token, expires_at = service.handle_callback(request.code, db)
        
        # Store OAuth credentials
        oauth_account = service.store_oauth_credentials(
            current_user.id,
            access_token,
            refresh_token,
            expires_at,
            db
        )
        
        # Get calendars
        calendars = service.get_calendars(access_token)
        
        return {
            "status": "success",
            "calendars": calendars,
            "oauth_account_id": str(oauth_account.id),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/google/select-calendar")
async def google_select_calendar(
    request: GoogleCalendarSelectRequest,
    oauth_account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Select a Google Calendar to sync."""
    try:
        # Verify OAuth account belongs to user
        oauth_account = db.query(UserOAuthAccount).filter(
            UserOAuthAccount.id == oauth_account_id,
            UserOAuthAccount.user_id == current_user.id,
            UserOAuthAccount.provider == "google",
        ).first()
        
        if not oauth_account:
            raise HTTPException(status_code=404, detail="OAuth account not found")
        
        # Check if calendar already integrated
        existing = db.query(CalendarIntegration).filter(
            CalendarIntegration.user_id == current_user.id,
            CalendarIntegration.provider == "google",
            CalendarIntegration.provider_calendar_id == request.calendar_id,
        ).first()
        
        if existing:
            db.delete(existing)
            db.commit()
        
        # Create new integration
        integration = CalendarIntegration(
            user_id=current_user.id,
            provider="google",
            provider_calendar_id=request.calendar_id,
            calendar_name=request.calendar_name,
            oauth_account_id=oauth_account.id,
            is_active=True,
            sync_enabled=False,
        )
        
        db.add(integration)
        db.commit()
        db.refresh(integration)
        
        return {
            "status": "success",
            "calendar_id": str(integration.id),
            "message": f"Calendar '{request.calendar_name}' selected"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/google/{calendar_id}/sync")
async def google_sync_calendar(
    calendar_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sync events from Google Calendar."""
    try:
        calendar = db.query(CalendarIntegration).filter(
            CalendarIntegration.id == calendar_id,
            CalendarIntegration.user_id == current_user.id,
            CalendarIntegration.provider == "google",
        ).first()
        
        if not calendar:
            raise HTTPException(status_code=404, detail="Calendar not found")
        
        # Get OAuth account
        oauth_account = calendar.oauth_account
        if not oauth_account or not oauth_account.access_token:
            raise HTTPException(status_code=400, detail="OAuth not configured")
        
        service = GoogleCalendarService()
        result = service.sync_calendar_events(
            current_user.id,
            calendar,
            oauth_account,
            db
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===== Outlook Calendar Routes =====

class MicrosoftAuthRequest(BaseModel):
    code: str


@router.get("/microsoft/authorize")
async def microsoft_authorize():
    """Get Microsoft OAuth authorization URL."""
    try:
        service = OutlookCalendarService()
        auth_url, state = service.get_authorization_url()
        return {
            "auth_url": auth_url,
            "state": state
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/microsoft/callback")
async def microsoft_callback(
    request: MicrosoftAuthRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Handle Microsoft OAuth callback and store credentials."""
    try:
        service = OutlookCalendarService()
        access_token, refresh_token, expires_at = service.handle_callback(request.code)
        
        # Store OAuth credentials
        oauth_account = service.store_oauth_credentials(
            current_user.id,
            access_token,
            refresh_token,
            expires_at,
            db
        )
        
        # Get calendars
        calendars = service.get_calendars(access_token)
        
        return {
            "status": "success",
            "calendars": calendars,
            "oauth_account_id": str(oauth_account.id),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/microsoft/select-calendar")
async def microsoft_select_calendar(
    request: GoogleCalendarSelectRequest,
    oauth_account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Select an Outlook Calendar to sync."""
    try:
        # Verify OAuth account belongs to user
        oauth_account = db.query(UserOAuthAccount).filter(
            UserOAuthAccount.id == oauth_account_id,
            UserOAuthAccount.user_id == current_user.id,
            UserOAuthAccount.provider == "microsoft",
        ).first()
        
        if not oauth_account:
            raise HTTPException(status_code=404, detail="OAuth account not found")
        
        # Check if calendar already integrated
        existing = db.query(CalendarIntegration).filter(
            CalendarIntegration.user_id == current_user.id,
            CalendarIntegration.provider == "microsoft",
            CalendarIntegration.provider_calendar_id == request.calendar_id,
        ).first()
        
        if existing:
            db.delete(existing)
            db.commit()
        
        # Create new integration
        integration = CalendarIntegration(
            user_id=current_user.id,
            provider="microsoft",
            provider_calendar_id=request.calendar_id,
            calendar_name=request.calendar_name,
            oauth_account_id=oauth_account.id,
            is_active=True,
            sync_enabled=False,
        )
        
        db.add(integration)
        db.commit()
        db.refresh(integration)
        
        return {
            "status": "success",
            "calendar_id": str(integration.id),
            "message": f"Calendar '{request.calendar_name}' selected"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/microsoft/{calendar_id}/sync")
async def microsoft_sync_calendar(
    calendar_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sync events from Outlook Calendar."""
    try:
        calendar = db.query(CalendarIntegration).filter(
            CalendarIntegration.id == calendar_id,
            CalendarIntegration.user_id == current_user.id,
            CalendarIntegration.provider == "microsoft",
        ).first()
        
        if not calendar:
            raise HTTPException(status_code=404, detail="Calendar not found")
        
        # Get OAuth account
        oauth_account = calendar.oauth_account
        if not oauth_account or not oauth_account.access_token:
            raise HTTPException(status_code=400, detail="OAuth not configured")
        
        service = OutlookCalendarService()
        result = service.sync_calendar_events(
            current_user.id,
            calendar,
            oauth_account,
            db
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===== Slack Routes =====

class SlackAuthRequest(BaseModel):
    code: str


class SlackCommandRequest(BaseModel):
    token: str
    team_id: str
    team_domain: str
    channel_id: str
    channel_name: str
    user_id: str
    user_name: str
    command: str
    text: str
    api_app_id: str
    response_url: str
    trigger_id: str
    x_request_timestamp: str
    x_slack_signature: str


@router.get("/slack/authorize")
async def slack_authorize():
    """Get Slack OAuth authorization URL."""
    try:
        service = SlackIntegrationService()
        auth_url = service.get_authorization_url()
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/slack/callback")
async def slack_callback(
    request: SlackAuthRequest,
    db: Session = Depends(get_db),
):
    """Handle Slack OAuth callback."""
    try:
        service = SlackIntegrationService()
        result = service.handle_oauth_callback(request.code)
        
        if result["status"] != "success":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        # Check if workspace already integrated
        existing = db.query(SlackIntegration).filter(
            SlackIntegration.workspace_id == result["workspace_id"]
        ).first()
        
        if existing:
            existing.bot_token = result["bot_token"]
            existing.app_id = result["app_id"]
            existing.workspace_name = result["workspace_name"]
            existing.is_active = True
            db.add(existing)
        else:
            integration = SlackIntegration(
                workspace_id=result["workspace_id"],
                workspace_name=result["workspace_name"],
                bot_token=result["bot_token"],
                app_id=result["app_id"],
                is_active=True,
            )
            db.add(integration)
        
        db.commit()
        
        return {
            "status": "success",
            "workspace_id": result["workspace_id"],
            "workspace_name": result["workspace_name"],
            "message": "Slack workspace integrated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/slack/commands/time")
async def slack_time_command(request: dict):
    """Handle /time capture command from Slack."""
    # Extract from request (Slack sends as form data)
    user_id = request.get("user_id")
    command_text = request.get("text")
    
    service = SlackIntegrationService()
    result = service.handle_time_capture_command(user_id, command_text)
    
    return result


@router.get("/slack/status")
async def slack_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get Slack integration status for current user."""
    binding = db.query(SlackUserBinding).filter(
        SlackUserBinding.user_id == current_user.id
    ).first()
    
    if not binding:
        return {"status": "not_connected"}
    
    return {
        "status": "connected",
        "slack_user_id": binding.slack_user_id,
        "slack_username": binding.slack_username,
        "daily_summary_enabled": binding.notify_daily_summary,
        "invoice_notifications_enabled": binding.notify_invoice_ready,
    }


class SlackNotificationPreferencesRequest(BaseModel):
    daily_summary: bool
    invoice_notifications: bool


@router.put("/slack/preferences")
async def update_slack_preferences(
    request: SlackNotificationPreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update Slack notification preferences."""
    binding = db.query(SlackUserBinding).filter(
        SlackUserBinding.user_id == current_user.id
    ).first()
    
    if not binding:
        raise HTTPException(status_code=404, detail="Slack not connected")
    
    binding.notify_daily_summary = request.daily_summary
    binding.notify_invoice_ready = request.invoice_notifications
    db.add(binding)
    db.commit()
    
    return {"status": "success", "message": "Preferences updated"}


# ===== Calendar Integration Management =====

@router.get("/calendars")
async def list_calendars(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all integrated calendars for current user."""
    calendars = db.query(CalendarIntegration).filter(
        CalendarIntegration.user_id == current_user.id
    ).all()
    
    return {
        "calendars": [
            {
                "id": str(cal.id),
                "provider": cal.provider,
                "calendar_name": cal.calendar_name,
                "is_active": cal.is_active,
                "sync_enabled": cal.sync_enabled,
                "last_sync_at": cal.last_sync_at.isoformat() if cal.last_sync_at else None,
            }
            for cal in calendars
        ]
    }


class CalendarEnableRequest(BaseModel):
    calendar_id: UUID
    sync_enabled: bool


@router.put("/calendars/{calendar_id}/enable")
async def enable_calendar_sync(
    calendar_id: UUID,
    request: CalendarEnableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enable or disable sync for a calendar."""
    calendar = db.query(CalendarIntegration).filter(
        CalendarIntegration.id == calendar_id,
        CalendarIntegration.user_id == current_user.id,
    ).first()
    
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    
    calendar.sync_enabled = request.sync_enabled
    db.add(calendar)
    db.commit()
    
    return {
        "status": "success",
        "calendar_id": str(calendar.id),
        "sync_enabled": calendar.sync_enabled,
    }


@router.delete("/calendars/{calendar_id}")
async def delete_calendar(
    calendar_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a calendar integration."""
    calendar = db.query(CalendarIntegration).filter(
        CalendarIntegration.id == calendar_id,
        CalendarIntegration.user_id == current_user.id,
    ).first()
    
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    
    db.delete(calendar)
    db.commit()
    
    return {"status": "success", "message": "Calendar deleted"}


@router.get("/calendars/{calendar_id}/events")
async def list_calendar_events(
    calendar_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List synced events from a calendar."""
    calendar = db.query(CalendarIntegration).filter(
        CalendarIntegration.id == calendar_id,
        CalendarIntegration.user_id == current_user.id,
    ).first()
    
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    
    events = db.query(SyncedCalendarEvent).filter(
        SyncedCalendarEvent.calendar_integration_id == calendar_id
    ).order_by(SyncedCalendarEvent.event_start.desc()).all()
    
    return {
        "events": [
            {
                "id": str(event.id),
                "summary": event.event_summary,
                "start": event.event_start.isoformat(),
                "end": event.event_end.isoformat(),
                "is_synced": event.is_synced,
                "time_entry_id": str(event.time_entry_id) if event.time_entry_id else None,
            }
            for event in events
        ]
    }


class ConvertEventRequest(BaseModel):
    synced_event_id: UUID
    project_id: UUID | None = None
    client_id: UUID | None = None


@router.post("/calendars/events/convert")
async def convert_event_to_time_entry(
    request: ConvertEventRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Convert a synced calendar event to a time entry."""
    from app.models.integrations import SyncedCalendarEvent
    
    event = db.query(SyncedCalendarEvent).filter(
        SyncedCalendarEvent.id == request.synced_event_id
    ).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Verify calendar belongs to user
    calendar = event.calendar_integration
    if calendar.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Use appropriate service to convert
    if calendar.provider == "google":
        service = GoogleCalendarService()
    else:
        service = OutlookCalendarService()
    
    time_entry = service.create_time_entry_from_event(
        current_user.id,
        event,
        request.project_id,
        request.client_id,
        db
    )
    
    if not time_entry:
        raise HTTPException(status_code=400, detail="Failed to convert event")
    
    return {
        "status": "success",
        "time_entry_id": str(time_entry.id),
        "message": "Event converted to time entry",
    }


# ===== Slack Time Capture Enhancement =====

class SlackTimeEntryRequest(BaseModel):
    duration_minutes: int
    description: str
    project_id: UUID | None = None
    client_id: UUID | None = None


@router.post("/slack/time-entry")
async def create_slack_time_entry(
    request: SlackTimeEntryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a time entry via Slack integration."""
    try:
        from datetime import datetime, timezone, timedelta
        
        now = datetime.now(timezone.utc)
        started_at = now - timedelta(minutes=request.duration_minutes)
        
        time_entry = TimeEntry(
            user_id=current_user.id,
            project_id=request.project_id,
            client_id=request.client_id,
            source="slack",
            started_at=started_at,
            ended_at=now,
            duration_minutes=request.duration_minutes,
            description=request.description,
            status="pending",
        )
        
        db.add(time_entry)
        db.commit()
        db.refresh(time_entry)
        
        # Send Slack notification
        slack_service = SlackIntegrationService()
        slack_service.notify_time_entry_created(time_entry, current_user, db)
        
        return {
            "status": "success",
            "time_entry_id": str(time_entry.id),
            "message": "Time entry created and Slack notification sent",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
