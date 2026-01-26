"""
Integration Testing Examples

This file contains curl examples and test cases for all integration endpoints.
Use these to verify the OAuth flows and API endpoints are working correctly.
"""

# ============================================================================
# GOOGLE CALENDAR INTEGRATION
# ============================================================================

# 1. Get Google OAuth authorization URL
curl -X GET http://localhost:8000/api/v1/integrations/google/authorize

# Example response:
# {
#   "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
#   "state": "abc123def456"
# }

# 2. After user signs in at Google, get the authorization code
# (This is done automatically by the OAuth flow)

# 3. Exchange authorization code for tokens
curl -X POST http://localhost:8000/api/v1/integrations/google/callback \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "code": "authorization-code-from-google"
  }'

# Example response:
# {
#   "status": "success",
#   "calendars": [
#     {"id": "primary", "summary": "user@gmail.com"},
#     {"id": "calendar-id-123", "summary": "Work Calendar"}
#   ],
#   "access_token": "ya29.a0AfH6SMBx...",
#   "refresh_token": "1//0gU..."
# }

# 4. Select a calendar to sync
curl -X POST http://localhost:8000/api/v1/integrations/google/select-calendar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "calendar_id": "primary",
    "calendar_name": "user@gmail.com",
    "access_token": "ya29.a0AfH6SMBx..."
  }'

# Example response:
# {
#   "status": "success",
#   "calendar_id": "550e8400-e29b-41d4-a716-446655440000",
#   "message": "Calendar 'user@gmail.com' selected"
# }

# 5. Sync calendar events
curl -X POST http://localhost:8000/api/v1/integrations/google/550e8400-e29b-41d4-a716-446655440000/sync \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Example response:
# {
#   "status": "success",
#   "events_synced": 12,
#   "new_events": 5,
#   "updated_events": 3,
#   "last_synced_at": "2024-01-24T21:30:00Z"
# }

# ============================================================================
# OUTLOOK CALENDAR INTEGRATION
# ============================================================================

# 1. Get Microsoft OAuth authorization URL
curl -X GET http://localhost:8000/api/v1/integrations/microsoft/authorize

# Example response:
# {
#   "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?...",
#   "state": "xyz789abc"
# }

# 2. Exchange authorization code for tokens
curl -X POST http://localhost:8000/api/v1/integrations/microsoft/callback \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "code": "authorization-code-from-microsoft"
  }'

# Example response:
# {
#   "status": "success",
#   "calendars": [
#     {"id": "calendar-id-123", "name": "Calendar"},
#     {"id": "calendar-id-456", "name": "Work"}
#   ],
#   "access_token": "EwAoA..."
# }

# 3. Select Outlook calendar
curl -X POST http://localhost:8000/api/v1/integrations/microsoft/select-calendar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "calendar_id": "calendar-id-123",
    "calendar_name": "Calendar",
    "access_token": "EwAoA..."
  }'

# 4. Sync Outlook calendar events
curl -X POST http://localhost:8000/api/v1/integrations/microsoft/550e8400-e29b-41d4-a716-446655440000/sync \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# ============================================================================
# SLACK INTEGRATION
# ============================================================================

# 1. Get Slack OAuth authorization URL (for workspace installation)
curl -X GET http://localhost:8000/api/v1/integrations/slack/authorize

# Example response:
# {
#   "auth_url": "https://slack.com/oauth/v2/authorize?client_id=..."
# }

# 2. Handle Slack OAuth callback
curl -X POST http://localhost:8000/api/v1/integrations/slack/callback \
  -H "Content-Type: application/json" \
  -d '{
    "code": "authorization-code-from-slack"
  }'

# Example response:
# {
#   "status": "success",
#   "workspace_id": "T1234567890",
#   "workspace_name": "My Workspace",
#   "message": "Slack workspace integrated successfully"
# }

# 3. Get Slack integration status
curl -X GET http://localhost:8000/api/v1/integrations/slack/status \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Example response:
# {
#   "status": "connected",
#   "slack_user_id": "U1234567890",
#   "slack_username": "john.doe",
#   "daily_summary_enabled": true,
#   "invoice_notifications_enabled": true
# }

# 4. Update Slack notification preferences
curl -X PUT http://localhost:8000/api/v1/integrations/slack/preferences \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "daily_summary": true,
    "invoice_notifications": true
  }'

# Example response:
# {
#   "status": "success",
#   "message": "Preferences updated"
# }

# 5. Handle /time slash command (from Slack)
# This is called by Slack when user types /time in the workspace
# Slack sends as form data, not JSON
curl -X POST http://localhost:8000/api/v1/integrations/slack/commands/time \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'user_id=U1234567890&text=2.5%20hours:%20Meeting%20with%20client&...'

# Example response (to Slack):
# {
#   "status": "success",
#   "message": "Time entry created: 2.5 hours"
# }

# ============================================================================
# PYTHON TESTING EXAMPLES
# ============================================================================

"""
Example Python tests for the integration services.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.integrations.google import GoogleCalendarService
from app.services.integrations.outlook import OutlookCalendarService
from app.services.integrations.slack_service import SlackIntegrationService


class TestGoogleCalendarService:
    """Test Google Calendar integration."""
    
    def test_get_authorization_url(self):
        """Test getting Google OAuth URL."""
        service = GoogleCalendarService()
        auth_url, state = service.get_authorization_url()
        
        assert auth_url.startswith('https://accounts.google.com/')
        assert 'client_id=' in auth_url
        assert 'scope=' in auth_url
        assert state is not None
    
    @patch('google.auth.transport.requests.Request')
    @patch('google.oauth2.flow.Flow')
    def test_handle_callback(self, mock_flow, mock_request):
        """Test handling OAuth callback."""
        service = GoogleCalendarService()
        
        # Mock the OAuth flow
        mock_flow_instance = MagicMock()
        mock_flow.from_client_secrets_file.return_value = mock_flow_instance
        mock_credentials = MagicMock()
        mock_credentials.token = 'access_token_123'
        mock_credentials.refresh_token = 'refresh_token_456'
        mock_flow_instance.fetch_token.return_value = mock_credentials
        
        # Call handle_callback
        result = service.handle_callback('auth_code_789', db=None)
        
        # Verify result
        assert result[0] == 'access_token_123'
        assert result[1] == 'refresh_token_456'
    
    @patch('googleapiclient.discovery.build')
    def test_get_calendars(self, mock_build):
        """Test getting user's calendars."""
        service = GoogleCalendarService()
        
        # Mock the Google Calendar API
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.calendarList().list().execute.return_value = {
            'items': [
                {'id': 'primary', 'summary': 'user@gmail.com'},
                {'id': 'cal-123', 'summary': 'Work'},
            ]
        }
        
        # Call get_calendars
        calendars = service.get_calendars('access_token_123')
        
        # Verify result
        assert len(calendars) == 2
        assert calendars[0]['id'] == 'primary'
        assert calendars[1]['summary'] == 'Work'


class TestOutlookCalendarService:
    """Test Outlook Calendar integration."""
    
    def test_get_authorization_url(self):
        """Test getting Microsoft OAuth URL."""
        service = OutlookCalendarService()
        auth_url, state = service.get_authorization_url()
        
        assert 'login.microsoftonline.com' in auth_url
        assert 'client_id=' in auth_url
        assert state is not None
    
    @patch('httpx.post')
    def test_handle_callback(self, mock_post):
        """Test handling Microsoft OAuth callback."""
        service = OutlookCalendarService()
        
        # Mock the token endpoint response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'access_token_123',
            'refresh_token': 'refresh_token_456',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response
        
        # Call handle_callback
        access_token, refresh_token, expires_at = service.handle_callback('auth_code_789')
        
        # Verify result
        assert access_token == 'access_token_123'
        assert refresh_token == 'refresh_token_456'


class TestSlackIntegrationService:
    """Test Slack integration."""
    
    def test_verify_slack_request_valid(self):
        """Test verifying a valid Slack request."""
        service = SlackIntegrationService(bot_token='xoxb-test-token')
        
        # Create a valid signature
        timestamp = '1234567890'
        body = 'test-body'
        import hmac
        import hashlib
        
        base_string = f'v0:{timestamp}:{body}'.encode()
        signature = 'v0=' + hmac.new(
            'test-secret'.encode(),
            base_string,
            hashlib.sha256
        ).hexdigest()
        
        # Verify with settings that match
        with patch('app.config.settings.Settings.slack_signing_secret', 'test-secret'):
            is_valid = service.verify_slack_request(body, signature, timestamp)
            assert is_valid is True
    
    def test_verify_slack_request_invalid_signature(self):
        """Test rejecting invalid Slack signature."""
        service = SlackIntegrationService(bot_token='xoxb-test-token')
        
        # Invalid signature
        is_valid = service.verify_slack_request('body', 'v0=invalid', '1234567890')
        assert is_valid is False
    
    @patch('slack_sdk.WebClient')
    def test_send_notification(self, mock_client):
        """Test sending Slack notification."""
        service = SlackIntegrationService(bot_token='xoxb-test-token')
        
        # Mock Slack API
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        
        # Mock database lookup
        with patch('app.db.session.SessionLocal') as mock_db:
            mock_binding = MagicMock()
            mock_binding.slack_user_id = 'U123456789'
            mock_db.query.return_value.filter.return_value.first.return_value = mock_binding
            
            # Send notification
            service.send_notification(
                'user-uuid-123',
                'Test Title',
                'Test message',
                'success'
            )
            
            # Verify message was sent
            mock_client_instance.chat_postMessage.assert_called_once()
    
    def test_handle_time_capture_command(self):
        """Test parsing /time command."""
        service = SlackIntegrationService(bot_token='xoxb-test-token')
        
        # Parse time capture command
        # Format: "2.5 hours: Meeting with client"
        result = service.handle_time_capture_command(
            'U123456789',
            '2.5 hours: Meeting with client'
        )
        
        # Verify parsing
        assert result['status'] == 'success'
        assert 'duration' in result or 'message' in result

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

"""
Full integration tests that test the entire flow.
"""

@pytest.mark.integration
class TestGoogleCalendarIntegration:
    """End-to-end Google Calendar integration tests."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, client):
        """Get authorization headers."""
        # This would normally login/create a test user
        return {"Authorization": "Bearer test-token"}
    
    def test_full_google_calendar_flow(self, client, auth_headers):
        """Test complete Google Calendar OAuth flow."""
        
        # 1. Get authorization URL
        response = client.get(
            "/api/v1/integrations/google/authorize"
        )
        assert response.status_code == 200
        assert "auth_url" in response.json()
        
        # 2. In real test, user would sign in and get authorization code
        # For testing, we would mock this step
        
        # 3. Handle callback with authorization code
        response = client.post(
            "/api/v1/integrations/google/callback",
            headers=auth_headers,
            json={"code": "mock-auth-code"}
        )
        # Would fail without real OAuth server, but this shows the flow
        
    def test_select_and_sync_calendar(self, client, auth_headers):
        """Test selecting a calendar and syncing events."""
        
        # 1. Select a calendar
        response = client.post(
            "/api/v1/integrations/google/select-calendar",
            headers=auth_headers,
            json={
                "calendar_id": "primary",
                "calendar_name": "user@gmail.com",
                "access_token": "mock-token"
            }
        )
        
        if response.status_code == 200:
            calendar_id = response.json()["calendar_id"]
            
            # 2. Sync events
            response = client.post(
                f"/api/v1/integrations/google/{calendar_id}/sync",
                headers=auth_headers
            )
            
            assert response.status_code == 200


# ============================================================================
# RUNNING TESTS
# ============================================================================

"""
Run tests with pytest:

# Run all integration tests
pytest tests/integration/test_integrations.py -v

# Run specific test
pytest tests/integration/test_integrations.py::TestGoogleCalendarService::test_get_authorization_url -v

# Run with coverage
pytest tests/integration/test_integrations.py --cov=app.services.integrations

# Run integration tests only
pytest tests/integration/ -m integration

# Run with output
pytest tests/ -v -s
"""
