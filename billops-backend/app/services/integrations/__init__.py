"""Google Calendar OAuth and event sync service."""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import UUID

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.oauthlib.flow import Flow
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth_httplib2 import AuthorizedHttp
import googleapiclient.discovery

from app.config.settings import get_settings
from app.db.session import SessionLocal
from app.models.user import UserOAuthAccount
from app.models.integrations import CalendarIntegration, SyncedCalendarEvent
from app.models.time_entry import TimeEntry
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarService:
    """Service for Google Calendar OAuth flow and event synchronization."""

    def __init__(self):
        self.settings = get_settings()

    def get_auth_flow(self) -> Flow:
        """Create and return Google OAuth flow for user authorization."""
        if not all([self.settings.google_client_id, self.settings.google_client_secret, self.settings.google_redirect_uri]):
            raise ValueError("Google OAuth credentials not configured")

        flow = Flow.from_client_config(
            client_config={
                "installed": {
                    "client_id": self.settings.google_client_id,
                    "client_secret": self.settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.settings.google_redirect_uri],
                }
            },
            scopes=CALENDAR_SCOPES,
            redirect_uri=self.settings.google_redirect_uri,
        )
        return flow

    def get_authorization_url(self) -> tuple[str, str]:
        """Get authorization URL for user to grant permissions.

        Returns:
            Tuple of (auth_url, state)
        """
        flow = self.get_auth_flow()
        auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")
        return auth_url, state

    def handle_callback(self, auth_code: str, db: Session) -> tuple[UserOAuthAccount, str]:
        """Handle OAuth callback and store credentials.

        Args:
            auth_code: Authorization code from Google
            db: Database session

        Returns:
            Tuple of (UserOAuthAccount, access_token)
        """
        flow = self.get_auth_flow()
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials

        access_token = credentials.token
        refresh_token = credentials.refresh_token
        expires_at = datetime.fromtimestamp(credentials.expiry.timestamp(), tz=timezone.utc) if credentials.expiry else None

        return access_token, refresh_token, expires_at

    def refresh_access_token(self, oauth_account: UserOAuthAccount) -> bool:
        """Refresh expired Google OAuth token.

        Args:
            oauth_account: UserOAuthAccount to refresh

        Returns:
            True if refresh successful, False otherwise
        """
        try:
            if not oauth_account.refresh_token:
                logger.error(f"No refresh token for {oauth_account.provider}")
                return False

            credentials = Credentials(
                token=oauth_account.access_token,
                refresh_token=oauth_account.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.settings.google_client_id,
                client_secret=self.settings.google_client_secret,
            )

            request = Request()
            credentials.refresh(request)

            # Update the token
            oauth_account.access_token = credentials.token
            oauth_account.expires_at = datetime.fromtimestamp(
                credentials.expiry.timestamp(), tz=timezone.utc
            ) if credentials.expiry else None

            return True
        except Exception as e:
            logger.error(f"Failed to refresh Google OAuth token: {e}")
            return False

    def get_calendar_service(self, access_token: str) -> Any:
        """Get authorized Google Calendar API service.

        Args:
            access_token: OAuth access token

        Returns:
            Google Calendar API service object
        """
        credentials = Credentials(token=access_token)
        service = googleapiclient.discovery.build("calendar", "v3", credentials=credentials)
        return service

    def get_calendars(self, access_token: str) -> list[dict[str, Any]]:
        """Get list of calendars from user's Google account.

        Args:
            access_token: OAuth access token

        Returns:
            List of calendar objects with id, summary, etc.
        """
        try:
            service = self.get_calendar_service(access_token)
            results = service.calendarList().list().execute()
            return results.get("items", [])
        except Exception as e:
            logger.error(f"Failed to fetch calendars: {e}")
            return []

    def sync_calendar_events(
        self,
        user_id: UUID,
        calendar_integration: CalendarIntegration,
        oauth_account: UserOAuthAccount,
        db: Session,
        days_back: int = 7,
        days_forward: int = 30,
    ) -> dict[str, Any]:
        """Sync events from Google Calendar to BillOps.

        Args:
            user_id: BillOps user ID
            calendar_integration: CalendarIntegration record
            oauth_account: UserOAuthAccount with OAuth tokens
            db: Database session
            days_back: Days in past to sync
            days_forward: Days in future to sync

        Returns:
            Dictionary with sync results
        """
        try:
            # Refresh token if needed
            if oauth_account.expires_at and oauth_account.expires_at < datetime.now(timezone.utc):
                if not self.refresh_access_token(oauth_account):
                    return {"status": "error", "message": "Failed to refresh OAuth token"}
                db.add(oauth_account)
                db.commit()

            service = self.get_calendar_service(oauth_account.access_token)

            # Set time bounds
            time_min = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
            time_max = (datetime.now(timezone.utc) + timedelta(days=days_forward)).isoformat()

            # Get events from calendar
            results = service.events().list(
                calendarId=calendar_integration.provider_calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
                showDeleted=False,
            ).execute()

            events = results.get("items", [])
            synced_count = 0
            skipped_count = 0

            for event in events:
                # Skip all-day events
                if "dateTime" not in event.get("start", {}):
                    skipped_count += 1
                    continue

                # Check if already synced
                existing = db.query(SyncedCalendarEvent).filter(
                    SyncedCalendarEvent.calendar_integration_id == calendar_integration.id,
                    SyncedCalendarEvent.provider_event_id == event["id"],
                ).first()

                if not existing:
                    # Create synced event record
                    start_dt = datetime.fromisoformat(event["start"]["dateTime"])
                    end_dt = datetime.fromisoformat(event["end"]["dateTime"])

                    synced_event = SyncedCalendarEvent(
                        calendar_integration_id=calendar_integration.id,
                        provider_event_id=event["id"],
                        event_summary=event.get("summary"),
                        event_description=event.get("description"),
                        event_start=start_dt,
                        event_end=end_dt,
                        is_synced=False,
                        last_synced_at=datetime.now(timezone.utc),
                    )
                    db.add(synced_event)
                    synced_count += 1
                else:
                    # Update existing event
                    existing.last_synced_at = datetime.now(timezone.utc)
                    db.add(existing)

            db.commit()
            calendar_integration.last_sync_at = datetime.now(timezone.utc)
            db.add(calendar_integration)
            db.commit()

            logger.info(
                f"Synced {synced_count} new events, skipped {skipped_count} "
                f"for user {user_id} from Google Calendar"
            )

            return {
                "status": "success",
                "synced_count": synced_count,
                "skipped_count": skipped_count,
                "last_sync_at": calendar_integration.last_sync_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error syncing Google Calendar: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def create_time_entry_from_event(
        self,
        user_id: UUID,
        synced_event: SyncedCalendarEvent,
        project_id: UUID | None = None,
        client_id: UUID | None = None,
        db: Session | None = None,
    ) -> TimeEntry | None:
        """Convert a synced calendar event to a time entry.

        Args:
            user_id: User creating the time entry
            synced_event: SyncedCalendarEvent to convert
            project_id: Project to assign (optional)
            client_id: Client to assign (optional)
            db: Database session

        Returns:
            Created TimeEntry or None if failed
        """
        if db is None:
            db = SessionLocal()

        try:
            duration_minutes = int(
                (synced_event.event_end - synced_event.event_start).total_seconds() / 60
            )

            time_entry = TimeEntry(
                user_id=user_id,
                project_id=project_id,
                client_id=client_id,
                source="calendar",
                started_at=synced_event.event_start,
                ended_at=synced_event.event_end,
                duration_minutes=duration_minutes,
                description=synced_event.event_summary,
                status="pending",
            )

            db.add(time_entry)
            db.flush()

            # Link synced event to time entry
            synced_event.time_entry_id = time_entry.id
            synced_event.is_synced = True
            db.add(synced_event)
            db.commit()

            logger.info(f"Created time entry {time_entry.id} from calendar event")
            return time_entry

        except Exception as e:
            logger.error(f"Failed to create time entry from event: {e}")
            db.rollback()
            return None
