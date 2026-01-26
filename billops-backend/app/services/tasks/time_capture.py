"""Time capture and tracking async tasks."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.services.notifications.email import EmailNotificationService
from app.services.notifications.slack import SlackNotificationService
from app.config.settings import Settings

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.services.tasks.time_capture.sync_time_entries_from_integrations",
    max_retries=3,
    default_retry_delay=60,
)
def sync_time_entries_from_integrations(self, user_id: Optional[str] = None):
    """
    Sync time entries from connected calendar and time tracking integrations.
    
    This task:
    - Fetches events from Google Calendar and Outlook
    - Converts events to time entries
    - Handles duplicates and updates
    - Stores in database
    
    Args:
        user_id: Optional user ID to sync for specific user (None = all users)
    
    Returns:
        dict: Sync summary with counts
    """
    db = SessionLocal()
    try:
        from app.services.integrations.calendar_sync import sync_user_calendar
        
        logger.info(f"Syncing time entries from integrations (user_id={user_id})")
        
        # Get users to sync
        if user_id:
            users = db.query(User).filter(User.id == user_id).all()
        else:
            # Get all active users with calendar integrations
            users = db.query(User).filter(User.is_active == True).all()
        
        sync_summary = {
            "users_synced": 0,
            "entries_created": 0,
            "entries_updated": 0,
            "errors": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        for user in users:
            try:
                result = sync_user_calendar(user, db)
                sync_summary["users_synced"] += 1
                sync_summary["entries_created"] += result.get("created", 0)
                sync_summary["entries_updated"] += result.get("updated", 0)
                logger.info(f"Synced calendar for user {user.id}: {result}")
            except Exception as e:
                logger.error(f"Error syncing calendar for user {user.id}: {e}", exc_info=True)
                sync_summary["errors"].append({
                    "user_id": str(user.id),
                    "error": str(e)
                })
        
        logger.info(f"Calendar sync completed: {sync_summary}")
        return sync_summary
        
    except Exception as exc:
        logger.error(f"Calendar sync failed: {exc}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.services.tasks.time_capture.aggregate_daily_time_entries",
    max_retries=3,
    default_retry_delay=120,
)
def aggregate_daily_time_entries(self, date_str: Optional[str] = None):
    """
    Aggregate time entries by day and user.
    
    This task:
    - Groups entries by user and day
    - Calculates total hours
    - Identifies gaps in tracking
    - Sends summary notifications
    
    Args:
        date_str: Date to aggregate (ISO format, default=yesterday)
    
    Returns:
        dict: Aggregation summary
    """
    db = SessionLocal()
    settings = Settings()
    
    try:
        # Parse date or use yesterday
        if date_str:
            target_date = datetime.fromisoformat(date_str).date()
        else:
            target_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()
        
        logger.info(f"Aggregating time entries for {target_date}")
        
        # Get all entries for the day
        start_of_day = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
        end_of_day = start_of_day + timedelta(days=1)
        
        entries = db.query(TimeEntry).filter(
            TimeEntry.start_time >= start_of_day,
            TimeEntry.start_time < end_of_day,
        ).all()
        
        # Group by user
        by_user = {}
        for entry in entries:
            user_id = str(entry.user_id)
            if user_id not in by_user:
                by_user[user_id] = {
                    "entries": [],
                    "total_hours": 0,
                    "total_billable_hours": 0,
                }
            
            duration = entry.duration_minutes / 60.0
            by_user[user_id]["entries"].append({
                "id": str(entry.id),
                "description": entry.description,
                "duration_hours": duration,
                "billable": entry.billable,
            })
            by_user[user_id]["total_hours"] += duration
            if entry.billable:
                by_user[user_id]["total_billable_hours"] += duration
        
        # Send notifications for users with activity
        notification_service = EmailNotificationService()
        for user_id_str, summary in by_user.items():
            try:
                user = db.query(User).filter(User.id == user_id_str).first()
                if user and user.email:
                    notification_service.send_time_entry_reminder(
                        recipient_email=user.email,
                        user_name=user.full_name or user.email.split("@")[0],
                        summary_date=target_date,
                        total_hours=summary["total_hours"],
                        entry_count=len(summary["entries"]),
                        entries=summary["entries"][:10],  # Top 10 entries
                    )
            except Exception as e:
                logger.warning(f"Failed to send time summary to user {user_id_str}: {e}")
        
        result = {
            "date": target_date.isoformat(),
            "users_with_entries": len(by_user),
            "total_entries": len(entries),
            "summary_by_user": by_user,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        logger.info(f"Daily aggregation completed: {len(entries)} entries for {len(by_user)} users")
        return result
        
    except Exception as exc:
        logger.error(f"Daily aggregation failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=120 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.services.tasks.time_capture.validate_time_entries",
    max_retries=2,
    default_retry_delay=60,
)
def validate_time_entries(self, user_id: str):
    """
    Validate time entries for a specific user.
    
    Checks for:
    - Missing descriptions
    - Overlapping entries
    - Excessively long entries
    - Untracked time gaps
    
    Args:
        user_id: User ID to validate
    
    Returns:
        dict: Validation results with issues found
    """
    db = SessionLocal()
    try:
        logger.info(f"Validating time entries for user {user_id}")
        
        issues = {
            "missing_descriptions": [],
            "overlapping_entries": [],
            "long_entries": [],
            "time_gaps": [],
        }
        
        # Get entries from last 7 days
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        entries = db.query(TimeEntry).filter(
            TimeEntry.user_id == user_id,
            TimeEntry.start_time >= seven_days_ago,
        ).order_by(TimeEntry.start_time).all()
        
        # Check for missing descriptions
        for entry in entries:
            if not entry.description or entry.description.strip() == "":
                issues["missing_descriptions"].append(str(entry.id))
        
        # Check for overlaps and gaps
        for i, entry in enumerate(entries):
            if not entry.description or entry.description.strip() == "":
                continue
                
            # Check for entries > 8 hours
            if entry.duration_minutes > 480:
                issues["long_entries"].append({
                    "entry_id": str(entry.id),
                    "hours": entry.duration_minutes / 60.0,
                })
            
            # Check for overlap with next entry
            if i < len(entries) - 1:
                next_entry = entries[i + 1]
                entry_end = entry.end_time or entry.start_time + timedelta(minutes=entry.duration_minutes)
                if entry_end > next_entry.start_time:
                    issues["overlapping_entries"].append({
                        "entry1": str(entry.id),
                        "entry2": str(next_entry.id),
                    })
                
                # Check for gaps > 30 minutes
                gap = (next_entry.start_time - entry_end).total_seconds() / 60
                if gap > 30:
                    issues["time_gaps"].append({
                        "after_entry": str(entry.id),
                        "gap_minutes": int(gap),
                    })
        
        result = {
            "user_id": user_id,
            "period": "last_7_days",
            "total_entries_checked": len(entries),
            "issues": issues,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        if any(issues.values()):
            logger.warning(f"Validation issues found for user {user_id}: {issues}")
        else:
            logger.info(f"Validation passed for user {user_id}")
        
        return result
        
    except Exception as exc:
        logger.error(f"Validation failed for user {user_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.services.tasks.time_capture.send_time_entry_reminders",
    max_retries=2,
    default_retry_delay=60,
)
def send_time_entry_reminders(self, reminder_type: str = "end_of_day"):
    """
    Send time entry reminders to users.
    
    Reminder types:
    - end_of_day: Remind to log time at end of day
    - missing_entries: Alert about missing entries
    - weekly_summary: Weekly time summary
    
    Args:
        reminder_type: Type of reminder to send
    
    Returns:
        dict: Reminders sent count
    """
    db = SessionLocal()
    settings = Settings()
    
    try:
        logger.info(f"Sending {reminder_type} time entry reminders")
        
        notification_service = EmailNotificationService()
        slack_service = SlackNotificationService(bot_token=settings.slack_bot_token)
        
        reminders_sent = {
            "email": 0,
            "slack": 0,
            "errors": [],
        }
        
        # Get active users
        users = db.query(User).filter(User.is_active == True).all()
        
        for user in users:
            try:
                # Send email reminder
                if user.email:
                    notification_service.send_alert_email(
                        recipient_email=user.email,
                        subject=f"Time Entry Reminder: {reminder_type.replace('_', ' ').title()}",
                        message=self._get_reminder_message(reminder_type, user),
                        alert_type="info",
                    )
                    reminders_sent["email"] += 1
                
                # Send Slack reminder if configured
                if settings.slack_bot_token and hasattr(user, 'slack_user_id'):
                    slack_service.send_notification(
                        user_id=user.slack_user_id,
                        text=f"Time Entry Reminder: {reminder_type.replace('_', ' ').title()}",
                    )
                    reminders_sent["slack"] += 1
                    
            except Exception as e:
                logger.warning(f"Failed to send reminder to user {user.id}: {e}")
                reminders_sent["errors"].append({
                    "user_id": str(user.id),
                    "error": str(e)
                })
        
        result = {
            "reminder_type": reminder_type,
            "total_reminders_sent": reminders_sent["email"] + reminders_sent["slack"],
            **reminders_sent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        logger.info(f"Reminders sent: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Reminder task failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()

    def _get_reminder_message(self, reminder_type: str, user) -> str:
        """Get reminder message by type."""
        messages = {
            "end_of_day": "Don't forget to log your time entries for today!",
            "missing_entries": "You have missing time entries. Please update them.",
            "weekly_summary": "Here's your weekly time summary. Please review and confirm.",
        }
        return messages.get(reminder_type, "Time entry reminder")
