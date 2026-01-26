"""Slack integration for notifications and time capture commands."""
from __future__ import annotations

import logging
import hmac
import hashlib
import json
from typing import Any
from uuid import UUID
from datetime import datetime, timezone

import httpx
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from app.config.settings import get_settings
from app.db.session import SessionLocal
from app.models.integrations import SlackIntegration, SlackUserBinding
from app.models.user import User
from app.models.time_entry import TimeEntry
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SlackIntegrationService:
    """Service for Slack workspace integration and notifications."""

    def __init__(self, bot_token: str | None = None):
        self.settings = get_settings()
        self.bot_token = bot_token or self.settings.slack_bot_token
        if self.bot_token:
            self.client = WebClient(token=self.bot_token)
        else:
            self.client = None

    def verify_slack_request(self, request_body: str, timestamp: str, signature: str) -> bool:
        """Verify that a request came from Slack.

        Args:
            request_body: Raw request body
            timestamp: Slack request timestamp
            signature: Slack request signature

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.settings.slack_signing_secret:
            logger.warning("Slack signing secret not configured")
            return False

        # Check timestamp is not too old (5 minutes)
        try:
            ts = int(timestamp)
            now = int(datetime.now(timezone.utc).timestamp())
            if abs(now - ts) > 300:
                return False
        except ValueError:
            return False

        # Calculate signature
        sig_basestring = f"v0:{timestamp}:{request_body}"
        my_signature = "v0=" + hmac.new(
            self.settings.slack_signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(my_signature, signature)

    def get_authorization_url(self) -> str:
        """Get Slack OAuth installation URL.

        Returns:
            Authorization URL for Slack app installation
        """
        if not all([self.settings.slack_client_id, self.settings.slack_redirect_uri]):
            raise ValueError("Slack OAuth credentials not configured")

        scopes = [
            "chat:write",
            "commands",
            "users:read",
            "users:read.email",
            "app_mentions:read",
        ]

        scope_str = " ".join(scopes)
        auth_url = (
            f"https://slack.com/oauth/v2/authorize"
            f"?client_id={self.settings.slack_client_id}"
            f"&scope={scope_str}"
            f"&redirect_uri={self.settings.slack_redirect_uri}"
        )

        return auth_url

    def handle_oauth_callback(self, auth_code: str) -> dict[str, Any]:
        """Handle Slack OAuth callback.

        Args:
            auth_code: Code from Slack OAuth callback

        Returns:
            Dictionary with bot token and workspace info
        """
        try:
            response = httpx.post(
                "https://slack.com/api/oauth.v2.access",
                data={
                    "client_id": self.settings.slack_client_id,
                    "client_secret": self.settings.slack_client_secret,
                    "code": auth_code,
                    "redirect_uri": self.settings.slack_redirect_uri,
                },
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                return {"status": "error", "message": data.get("error", "Unknown error")}

            return {
                "status": "success",
                "bot_token": data.get("bot_token"),
                "app_id": data.get("app_id"),
                "workspace_id": data.get("team", {}).get("id"),
                "workspace_name": data.get("team", {}).get("name"),
            }
        except Exception as e:
            logger.error(f"Failed to handle Slack OAuth callback: {e}")
            return {"status": "error", "message": str(e)}

    def send_message(
        self,
        channel: str,
        text: str,
        blocks: list[dict] | None = None,
        thread_ts: str | None = None,
    ) -> bool:
        """Send a message to a Slack channel.

        Args:
            channel: Channel ID or name
            text: Message text
            blocks: Slack block kit blocks (optional)
            thread_ts: Thread timestamp for threading (optional)

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Slack client not configured")
            return False

        try:
            self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks,
                thread_ts=thread_ts,
            )
            return True
        except SlackApiError as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False

    def send_notification(
        self,
        user_id: UUID,
        title: str,
        message: str,
        notification_type: str = "info",
        db: Session | None = None,
    ) -> bool:
        """Send a notification to a user via Slack.

        Args:
            user_id: BillOps user ID
            title: Notification title
            message: Notification message
            notification_type: Type (info, success, warning, error)
            db: Database session

        Returns:
            True if successful, False otherwise
        """
        if db is None:
            db = SessionLocal()

        try:
            binding = db.query(SlackUserBinding).filter(
                SlackUserBinding.user_id == user_id
            ).first()

            if not binding:
                logger.debug(f"No Slack binding for user {user_id}")
                return False

            # Color based on notification type
            colors = {
                "success": "#36a64f",
                "warning": "#ff9900",
                "error": "#ff0000",
                "info": "#0099ff",
            }

            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{title}*\n{message}",
                    },
                },
            ]

            return self.send_message(
                channel=binding.slack_user_id,
                text=title,
                blocks=blocks,
            )

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    def notify_time_entry_created(
        self,
        time_entry: TimeEntry,
        user: User,
        db: Session | None = None,
    ) -> bool:
        """Send notification that a time entry was created.

        Args:
            time_entry: Created TimeEntry
            user: User who created it
            db: Database session

        Returns:
            True if notification sent successfully
        """
        duration_hours = time_entry.duration_minutes / 60
        message = (
            f"New time entry created: *{time_entry.description or 'Work'}*\n"
            f"Duration: {duration_hours:.1f} hours\n"
            f"Date: {time_entry.started_at.strftime('%Y-%m-%d %H:%M')}"
        )

        return self.send_notification(
            user_id=user.id,
            title="⏱️ Time Entry Created",
            message=message,
            notification_type="success",
            db=db,
        )

    def notify_invoice_ready(
        self,
        invoice_number: str,
        total_cents: int,
        user_id: UUID,
        db: Session | None = None,
    ) -> bool:
        """Send notification that an invoice is ready.

        Args:
            invoice_number: Invoice number
            total_cents: Invoice total in cents
            user_id: User to notify
            db: Database session

        Returns:
            True if notification sent successfully
        """
        total_dollars = total_cents / 100
        message = (
            f"Invoice *{invoice_number}* is ready!\n"
            f"Total: *${total_dollars:,.2f}*"
        )

        return self.send_notification(
            user_id=user_id,
            title="📄 Invoice Ready",
            message=message,
            notification_type="success",
            db=db,
        )

    def send_daily_summary(
        self,
        user_id: UUID,
        total_hours: float,
        entry_count: int,
        db: Session | None = None,
    ) -> bool:
        """Send daily time summary to user.

        Args:
            user_id: User to notify
            total_hours: Total hours worked
            entry_count: Number of time entries
            db: Database session

        Returns:
            True if notification sent successfully
        """
        message = (
            f"Daily Summary:\n"
            f"• Entries: {entry_count}\n"
            f"• Total: {total_hours:.1f} hours"
        )

        return self.send_notification(
            user_id=user_id,
            title="📊 Daily Time Summary",
            message=message,
            notification_type="info",
            db=db,
        )

    def handle_time_capture_command(
        self,
        slack_user_id: str,
        command_text: str,
        db: Session | None = None,
    ) -> dict[str, Any]:
        """Handle /time capture slash command.

        Args:
            slack_user_id: Slack user ID
            command_text: Command text (e.g., "2 hours: Meeting with client")
            db: Database session

        Returns:
            Response dict with status and message
        """
        if db is None:
            db = SessionLocal()

        try:
            # Find user binding
            binding = db.query(SlackUserBinding).filter(
                SlackUserBinding.slack_user_id == slack_user_id
            ).first()

            if not binding:
                return {
                    "response_type": "ephemeral",
                    "text": "Please link your BillOps account first. Visit the settings.",
                }

            # Parse command text: "2 hours: Meeting with client"
            parts = command_text.split(":", 1)
            if len(parts) != 2:
                return {
                    "response_type": "ephemeral",
                    "text": "Format: `/time 2.5 hours: Description`",
                }

            duration_str = parts[0].strip()
            description = parts[1].strip()

            # Parse duration
            try:
                duration_hours = float(duration_str.split()[0])
                duration_minutes = int(duration_hours * 60)
            except (ValueError, IndexError):
                return {
                    "response_type": "ephemeral",
                    "text": "Invalid duration. Use format: `/time 2.5 hours: Description`",
                }

            # Create time entry
            user = db.query(User).filter(User.id == binding.user_id).first()
            if not user:
                return {
                    "response_type": "ephemeral",
                    "text": "User not found",
                }

            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            started_at = now - timedelta(minutes=duration_minutes)

            time_entry = TimeEntry(
                user_id=binding.user_id,
                source="slack",
                started_at=started_at,
                ended_at=now,
                duration_minutes=duration_minutes,
                description=description,
                status="pending",
            )

            db.add(time_entry)
            db.commit()

            return {
                "response_type": "in_channel",
                "text": f"✅ Time entry created: *{description}* ({duration_hours} hours)",
            }

        except Exception as e:
            logger.error(f"Failed to handle time capture command: {e}")
            return {
                "response_type": "ephemeral",
                "text": f"Error: {str(e)}",
            }

    def list_workspace_users(self) -> list[dict[str, Any]]:
        """Get list of users in Slack workspace.

        Returns:
            List of user objects
        """
        if not self.client:
            logger.error("Slack client not configured")
            return []

        try:
            response = self.client.users_list()
            return response.get("members", [])
        except SlackApiError as e:
            logger.error(f"Failed to list Slack users: {e}")
            return []
