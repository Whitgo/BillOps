"""Tests for calendar and Slack integrations."""
import json
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock

import pytest
from sqlalchemy.orm import Session

from app.models.user import User, UserOAuthAccount
from app.models.integrations import (
    CalendarIntegration,
    SyncedCalendarEvent,
    SlackIntegration,
    SlackUserBinding,
)
from app.models.time_entry import TimeEntry
from app.services.integrations.google import GoogleCalendarService
from app.services.integrations.outlook import OutlookCalendarService
from app.services.integrations.slack_service import SlackIntegrationService


class TestGoogleCalendarService:
    """Tests for Google Calendar integration."""

    def test_get_authorization_url(self, monkeypatch):
        """Test getting authorization URL."""
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test_secret")
        monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost/callback")

        service = GoogleCalendarService()
        auth_url, state = service.get_authorization_url()

        assert "accounts.google.com" in auth_url
        assert "scope=https" in auth_url
        assert state is not None
        assert len(state) > 0

    def test_get_calendars(self, monkeypatch):
        """Test retrieving calendar list."""
        service = GoogleCalendarService()

        with patch("app.services.integrations.google.googleapiclient.discovery.build") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service

            mock_service.calendarList().list().execute.return_value = {
                "items": [
                    {
                        "id": "primary",
                        "summary": "Primary Calendar",
                        "primary": True,
                    },
                    {
                        "id": "secondary123",
                        "summary": "Work Calendar",
                        "primary": False,
                    },
                ]
            }

            calendars = service.get_calendars("mock_token")

            assert len(calendars) == 2
            assert calendars[0]["summary"] == "Primary Calendar"
            assert calendars[1]["summary"] == "Work Calendar"

    def test_sync_calendar_events(self, db_session: Session, monkeypatch):
        """Test syncing events from Google Calendar."""
        # Create test user and integration
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password="hash",
        )
        db_session.add(user)

        oauth_account = UserOAuthAccount(
            id=uuid.uuid4(),
            user_id=user.id,
            provider="google",
            access_token="test_token",
            refresh_token="test_refresh",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(oauth_account)

        calendar = CalendarIntegration(
            id=uuid.uuid4(),
            user_id=user.id,
            provider="google",
            provider_calendar_id="primary",
            calendar_name="Primary Calendar",
            oauth_account_id=oauth_account.id,
            is_active=True,
            sync_enabled=True,
        )
        db_session.add(calendar)
        db_session.commit()

        service = GoogleCalendarService()

        with patch("app.services.integrations.google.googleapiclient.discovery.build") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service

            now = datetime.now(timezone.utc)
            event_start = now + timedelta(hours=1)
            event_end = now + timedelta(hours=2)

            mock_service.events().list().execute.return_value = {
                "items": [
                    {
                        "id": "event1",
                        "summary": "Team Meeting",
                        "description": "Weekly sync",
                        "start": {"dateTime": event_start.isoformat()},
                        "end": {"dateTime": event_end.isoformat()},
                    }
                ]
            }

            result = service.sync_calendar_events(
                user.id,
                calendar,
                oauth_account,
                db_session,
            )

            assert result["status"] == "success"
            assert result["synced_count"] == 1
            assert result["skipped_count"] == 0

            # Verify event was synced
            synced_event = db_session.query(SyncedCalendarEvent).filter(
                SyncedCalendarEvent.calendar_integration_id == calendar.id
            ).first()

            assert synced_event is not None
            assert synced_event.event_summary == "Team Meeting"
            assert synced_event.provider_event_id == "event1"

    def test_create_time_entry_from_event(self, db_session: Session):
        """Test converting calendar event to time entry."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password="hash",
        )
        db_session.add(user)

        calendar = CalendarIntegration(
            id=uuid.uuid4(),
            user_id=user.id,
            provider="google",
            provider_calendar_id="primary",
        )
        db_session.add(calendar)

        now = datetime.now(timezone.utc)
        event_start = now - timedelta(hours=2)
        event_end = now - timedelta(hours=1)

        synced_event = SyncedCalendarEvent(
            id=uuid.uuid4(),
            calendar_integration_id=calendar.id,
            provider_event_id="event1",
            event_summary="Client Meeting",
            event_start=event_start,
            event_end=event_end,
        )
        db_session.add(synced_event)
        db_session.commit()

        service = GoogleCalendarService()
        time_entry = service.create_time_entry_from_event(
            user.id,
            synced_event,
            db=db_session,
        )

        assert time_entry is not None
        assert time_entry.description == "Client Meeting"
        assert time_entry.duration_minutes == 60
        assert time_entry.source == "calendar"

        # Verify synced event was linked
        db_session.refresh(synced_event)
        assert synced_event.time_entry_id == time_entry.id
        assert synced_event.is_synced is True

    def test_store_oauth_credentials(self, db_session: Session, monkeypatch):
        """Test storing OAuth credentials."""
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test_secret")
        monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost/callback")

        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password="hash",
        )
        db_session.add(user)
        db_session.commit()

        service = GoogleCalendarService()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        oauth_account = service.store_oauth_credentials(
            user.id,
            "test_access_token",
            "test_refresh_token",
            expires_at,
            db_session,
        )

        assert oauth_account.user_id == user.id
        assert oauth_account.provider == "google"
        assert oauth_account.access_token == "test_access_token"
        assert oauth_account.refresh_token == "test_refresh_token"

        # Test updating existing
        oauth_account2 = service.store_oauth_credentials(
            user.id,
            "new_access_token",
            "new_refresh_token",
            expires_at,
            db_session,
        )

        assert oauth_account2.id == oauth_account.id
        assert oauth_account2.access_token == "new_access_token"


class TestOutlookCalendarService:
    """Tests for Outlook Calendar integration."""

    def test_get_authorization_url(self, monkeypatch):
        """Test getting Microsoft authorization URL."""
        monkeypatch.setenv("MICROSOFT_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("MICROSOFT_REDIRECT_URI", "http://localhost/callback")
        monkeypatch.setenv("MICROSOFT_TENANT_ID", "common")

        service = OutlookCalendarService()
        auth_url, state = service.get_authorization_url()

        assert "login.microsoftonline.com" in auth_url
        assert "test_client_id" in auth_url
        assert state is not None

    def test_sync_outlook_events(self, db_session: Session):
        """Test syncing Outlook calendar events."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password="hash",
        )
        db_session.add(user)

        oauth_account = UserOAuthAccount(
            id=uuid.uuid4(),
            user_id=user.id,
            provider="microsoft",
            access_token="test_token",
            refresh_token="test_refresh",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(oauth_account)

        calendar = CalendarIntegration(
            id=uuid.uuid4(),
            user_id=user.id,
            provider="microsoft",
            provider_calendar_id="AQMkADAwATZhZmE=",
            calendar_name="Calendar",
            oauth_account_id=oauth_account.id,
        )
        db_session.add(calendar)
        db_session.commit()

        service = OutlookCalendarService()

        with patch("app.services.integrations.outlook.httpx.get") as mock_get:
            now = datetime.now(timezone.utc)
            event_start = now + timedelta(hours=1)
            event_end = now + timedelta(hours=2)

            mock_response = MagicMock()
            mock_response.json.return_value = {
                "value": [
                    {
                        "id": "outlook_event_1",
                        "subject": "Outlook Meeting",
                        "bodyPreview": "Meeting details",
                        "start": {"dateTime": event_start.isoformat()},
                        "end": {"dateTime": event_end.isoformat()},
                    }
                ]
            }
            mock_get.return_value = mock_response

            result = service.sync_calendar_events(
                user.id,
                calendar,
                oauth_account,
                db_session,
            )

            assert result["status"] == "success"
            assert result["synced_count"] == 1


class TestSlackIntegrationService:
    """Tests for Slack integration."""

    def test_verify_slack_request(self, monkeypatch):
        """Test Slack request verification."""
        monkeypatch.setenv("SLACK_SIGNING_SECRET", "test_secret")

        service = SlackIntegrationService()

        timestamp = str(int(datetime.now(timezone.utc).timestamp()))
        body = "v0:test:command"

        import hmac
        import hashlib

        sig_basestring = f"v0:{timestamp}:{body}"
        signature = "v0=" + hmac.new(
            b"test_secret",
            sig_basestring.encode(),
            hashlib.sha256,
        ).hexdigest()

        assert service.verify_slack_request(body, timestamp, signature) is True
        assert service.verify_slack_request(body, timestamp, "v0=invalid") is False

    def test_handle_time_capture_command(self, db_session: Session):
        """Test handling Slack time capture command."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password="hash",
        )
        db_session.add(user)

        slack_integration = SlackIntegration(
            id=uuid.uuid4(),
            workspace_id="T123456",
            workspace_name="Test Workspace",
            bot_token="xoxb-test",
            app_id="A123456",
        )
        db_session.add(slack_integration)

        binding = SlackUserBinding(
            id=uuid.uuid4(),
            user_id=user.id,
            slack_integration_id=slack_integration.id,
            slack_user_id="U123456",
            slack_username="testuser",
        )
        db_session.add(binding)
        db_session.commit()

        service = SlackIntegrationService()
        result = service.handle_time_capture_command(
            "U123456",
            "2.5 hours: Client meeting",
            db_session,
        )

        assert result["response_type"] == "in_channel"
        assert "✅" in result["text"]
        assert "2.5 hours" in result["text"]

        # Verify time entry was created
        time_entry = db_session.query(TimeEntry).filter(
            TimeEntry.user_id == user.id
        ).first()

        assert time_entry is not None
        assert time_entry.duration_minutes == 150
        assert time_entry.description == "Client meeting"
        assert time_entry.source == "slack"

    def test_handle_invalid_time_command(self, db_session: Session):
        """Test handling invalid time capture command."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password="hash",
        )
        db_session.add(user)

        slack_integration = SlackIntegration(
            id=uuid.uuid4(),
            workspace_id="T123456",
            workspace_name="Test Workspace",
            bot_token="xoxb-test",
            app_id="A123456",
        )
        db_session.add(slack_integration)

        binding = SlackUserBinding(
            id=uuid.uuid4(),
            user_id=user.id,
            slack_integration_id=slack_integration.id,
            slack_user_id="U123456",
            slack_username="testuser",
        )
        db_session.add(binding)
        db_session.commit()

        service = SlackIntegrationService()

        # Invalid format
        result = service.handle_time_capture_command(
            "U123456",
            "invalid format",
            db_session,
        )

        assert result["response_type"] == "ephemeral"
        assert "Format" in result["text"]

    def test_send_notification(self, db_session: Session):
        """Test sending Slack notification."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password="hash",
        )
        db_session.add(user)

        slack_integration = SlackIntegration(
            id=uuid.uuid4(),
            workspace_id="T123456",
            workspace_name="Test Workspace",
            bot_token="xoxb-test",
            app_id="A123456",
        )
        db_session.add(slack_integration)

        binding = SlackUserBinding(
            id=uuid.uuid4(),
            user_id=user.id,
            slack_integration_id=slack_integration.id,
            slack_user_id="U123456",
            slack_username="testuser",
        )
        db_session.add(binding)
        db_session.commit()

        service = SlackIntegrationService()

        with patch.object(service.client, "chat_postMessage") as mock_post:
            result = service.send_notification(
                user.id,
                "Test Title",
                "Test message",
                "success",
                db_session,
            )

            assert result is True
            mock_post.assert_called_once()

    def test_notify_time_entry_created(self, db_session: Session):
        """Test time entry notification."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password="hash",
        )
        db_session.add(user)

        slack_integration = SlackIntegration(
            id=uuid.uuid4(),
            workspace_id="T123456",
            workspace_name="Test Workspace",
            bot_token="xoxb-test",
            app_id="A123456",
        )
        db_session.add(slack_integration)

        binding = SlackUserBinding(
            id=uuid.uuid4(),
            user_id=user.id,
            slack_integration_id=slack_integration.id,
            slack_user_id="U123456",
            slack_username="testuser",
        )
        db_session.add(binding)
        db_session.commit()

        now = datetime.now(timezone.utc)
        time_entry = TimeEntry(
            id=uuid.uuid4(),
            user_id=user.id,
            source="slack",
            started_at=now - timedelta(hours=2),
            ended_at=now - timedelta(hours=1),
            duration_minutes=60,
            description="Client Meeting",
            status="pending",
        )
        db_session.add(time_entry)
        db_session.commit()

        service = SlackIntegrationService()

        with patch.object(service.client, "chat_postMessage") as mock_post:
            result = service.notify_time_entry_created(time_entry, user, db_session)

            assert result is True
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "Client Meeting" in str(call_args)


class TestCalendarIntegrationAPI:
    """Tests for calendar integration API endpoints."""

    def test_google_authorize_endpoint(self, client, monkeypatch):
        """Test Google authorization endpoint."""
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test_secret")
        monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost/callback")

        response = client.get("/api/v1/integrations/google/authorize")

        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        assert "state" in data
        assert "accounts.google.com" in data["auth_url"]

    def test_list_calendars_endpoint(self, client, current_user, monkeypatch):
        """Test listing integrated calendars."""
        response = client.get(
            "/api/v1/integrations/calendars",
            headers={"Authorization": f"Bearer {current_user['token']}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "calendars" in data
        assert isinstance(data["calendars"], list)

    def test_get_calendar_events_endpoint(self, client, current_user, db_session):
        """Test getting calendar events."""
        user_id = uuid.UUID(current_user["id"])

        # Create test calendar
        calendar = CalendarIntegration(
            id=uuid.uuid4(),
            user_id=user_id,
            provider="google",
            provider_calendar_id="primary",
            calendar_name="Primary Calendar",
        )
        db_session.add(calendar)
        db_session.commit()

        response = client.get(
            f"/api/v1/integrations/calendars/{calendar.id}/events",
            headers={"Authorization": f"Bearer {current_user['token']}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "events" in data

    def test_delete_calendar_endpoint(self, client, current_user, db_session):
        """Test deleting a calendar."""
        user_id = uuid.UUID(current_user["id"])

        calendar = CalendarIntegration(
            id=uuid.uuid4(),
            user_id=user_id,
            provider="google",
            provider_calendar_id="primary",
            calendar_name="Primary Calendar",
        )
        db_session.add(calendar)
        db_session.commit()

        calendar_id = calendar.id

        response = client.delete(
            f"/api/v1/integrations/calendars/{calendar_id}",
            headers={"Authorization": f"Bearer {current_user['token']}"},
        )

        assert response.status_code == 200

        # Verify deleted
        calendar = db_session.query(CalendarIntegration).filter(
            CalendarIntegration.id == calendar_id
        ).first()
        assert calendar is None
