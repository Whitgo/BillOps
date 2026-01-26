"""Outlook Calendar integration using Microsoft Graph API."""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import UUID
import json

import httpx
from azure.identity import ClientSecretCredential
from msgraph.core import GraphClient

from app.config.settings import get_settings
from app.db.session import SessionLocal
from app.models.user import User, UserOAuthAccount
from app.models.integrations import CalendarIntegration, SyncedCalendarEvent
from app.models.time_entry import TimeEntry
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class OutlookCalendarService:
    """Service for Outlook/Microsoft Calendar OAuth flow and event synchronization."""

    def __init__(self):
        self.settings = get_settings()
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        self.auth_endpoint = "https://login.microsoftonline.com"

    def get_authorization_url(self) -> tuple[str, str]:
        """Get authorization URL for user to grant permissions.

        Returns:
            Tuple of (auth_url, state)
        """
        if not all([self.settings.microsoft_client_id, self.settings.microsoft_redirect_uri]):
            raise ValueError("Microsoft OAuth credentials not configured")

        import uuid
        state = str(uuid.uuid4())

        auth_url = (
            f"{self.auth_endpoint}/{self.settings.microsoft_tenant_id}/oauth2/v2.0/authorize"
            f"?client_id={self.settings.microsoft_client_id}"
            f"&redirect_uri={self.settings.microsoft_redirect_uri}"
            f"&response_type=code"
            f"&scope=https://graph.microsoft.com/.default"
            f"&state={state}"
        )

        return auth_url, state

    def handle_callback(self, auth_code: str) -> tuple[str, str, datetime]:
        """Handle OAuth callback and exchange code for token.

        Args:
            auth_code: Authorization code from Microsoft

        Returns:
            Tuple of (access_token, refresh_token, expires_at)
        """
        if not all([self.settings.microsoft_client_id, self.settings.microsoft_client_secret]):
            raise ValueError("Microsoft OAuth credentials not configured")

        token_url = f"{self.auth_endpoint}/{self.settings.microsoft_tenant_id}/oauth2/v2.0/token"

        payload = {
            "client_id": self.settings.microsoft_client_id,
            "client_secret": self.settings.microsoft_client_secret,
            "code": auth_code,
            "redirect_uri": self.settings.microsoft_redirect_uri,
            "grant_type": "authorization_code",
        }

        response = httpx.post(token_url, data=payload)
        response.raise_for_status()
        data = response.json()

        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        expires_in = data.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        return access_token, refresh_token, expires_at

    def store_oauth_credentials(
        self,
        user_id: UUID,
        access_token: str,
        refresh_token: str,
        expires_at: datetime,
        db: Session,
    ) -> UserOAuthAccount:
        """Store Microsoft OAuth credentials for a user.

        Args:
            user_id: BillOps user ID
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_at: Token expiration time
            db: Database session

        Returns:
            Created or updated UserOAuthAccount
        """
        # Check if existing
        oauth_account = db.query(UserOAuthAccount).filter(
            UserOAuthAccount.user_id == user_id,
            UserOAuthAccount.provider == "microsoft",
        ).first()

        if not oauth_account:
            oauth_account = UserOAuthAccount(
                user_id=user_id,
                provider="microsoft",
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )
            db.add(oauth_account)
        else:
            oauth_account.access_token = access_token
            oauth_account.refresh_token = refresh_token
            oauth_account.expires_at = expires_at
            db.add(oauth_account)

        db.commit()
        db.refresh(oauth_account)
        return oauth_account

    def refresh_access_token(self, oauth_account: UserOAuthAccount) -> bool:
        """Refresh expired Microsoft OAuth token.

        Args:
            oauth_account: UserOAuthAccount to refresh

        Returns:
            True if refresh successful, False otherwise
        """
        try:
            if not oauth_account.refresh_token:
                logger.error("No refresh token for Microsoft OAuth")
                return False

            if not all([self.settings.microsoft_client_id, self.settings.microsoft_client_secret]):
                logger.error("Microsoft OAuth credentials not configured")
                return False

            token_url = f"{self.auth_endpoint}/{self.settings.microsoft_tenant_id}/oauth2/v2.0/token"

            payload = {
                "client_id": self.settings.microsoft_client_id,
                "client_secret": self.settings.microsoft_client_secret,
                "refresh_token": oauth_account.refresh_token,
                "grant_type": "refresh_token",
            }

            response = httpx.post(token_url, data=payload)
            response.raise_for_status()
            data = response.json()

            oauth_account.access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            oauth_account.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            return True
        except Exception as e:
            logger.error(f"Failed to refresh Microsoft OAuth token: {e}")
            return False

    def get_calendars(self, access_token: str) -> list[dict[str, Any]]:
        """Get list of calendars from user's Microsoft account.

        Args:
            access_token: OAuth access token

        Returns:
            List of calendar objects with id, name, etc.
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = httpx.get(f"{self.graph_endpoint}/me/calendars", headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("value", [])
        except Exception as e:
            logger.error(f"Failed to fetch calendars from Microsoft: {e}")
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
        """Sync events from Outlook Calendar to BillOps.

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

            headers = {"Authorization": f"Bearer {oauth_account.access_token}"}

            # Set time bounds
            time_min = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
            time_max = (datetime.now(timezone.utc) + timedelta(days=days_forward)).isoformat()

            # Get events from calendar
            query_params = {
                "$filter": f"start/dateTime ge '{time_min}' and start/dateTime le '{time_max}'",
                "$orderby": "start/dateTime",
            }

            response = httpx.get(
                f"{self.graph_endpoint}/me/calendars/{calendar_integration.provider_calendar_id}/events",
                headers=headers,
                params=query_params,
            )
            response.raise_for_status()
            data = response.json()
            events = data.get("value", [])

            synced_count = 0
            skipped_count = 0

            for event in events:
                # Skip events without start/end times
                if not event.get("start") or not event.get("end"):
                    skipped_count += 1
                    continue

                # Check if already synced
                existing = db.query(SyncedCalendarEvent).filter(
                    SyncedCalendarEvent.calendar_integration_id == calendar_integration.id,
                    SyncedCalendarEvent.provider_event_id == event["id"],
                ).first()

                if not existing:
                    # Parse Microsoft date format
                    start_str = event["start"]["dateTime"]
                    end_str = event["end"]["dateTime"]

                    # Remove timezone offset for parsing
                    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))

                    synced_event = SyncedCalendarEvent(
                        calendar_integration_id=calendar_integration.id,
                        provider_event_id=event["id"],
                        event_summary=event.get("subject"),
                        event_description=event.get("bodyPreview"),
                        event_start=start_dt,
                        event_end=end_dt,
                        is_synced=False,
                        last_synced_at=datetime.now(timezone.utc),
                    )
                    db.add(synced_event)
                    synced_count += 1
                else:
                    existing.last_synced_at = datetime.now(timezone.utc)
                    db.add(existing)

            db.commit()
            calendar_integration.last_sync_at = datetime.now(timezone.utc)
            db.add(calendar_integration)
            db.commit()

            logger.info(
                f"Synced {synced_count} new events, skipped {skipped_count} "
                f"for user {user_id} from Outlook Calendar"
            )

            return {
                "status": "success",
                "synced_count": synced_count,
                "skipped_count": skipped_count,
                "last_sync_at": calendar_integration.last_sync_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error syncing Outlook Calendar: {e}", exc_info=True)
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

            synced_event.time_entry_id = time_entry.id
            synced_event.is_synced = True
            db.add(synced_event)
            db.commit()

            logger.info(f"Created time entry {time_entry.id} from Outlook event")
            return time_entry

        except Exception as e:
            logger.error(f"Failed to create time entry from event: {e}")
            db.rollback()
            return None
