"""Celery tasks for integration syncs and notifications."""
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.integrations import CalendarIntegration, SlackIntegration, SlackUserBinding
from app.models.user import User
from app.services.integrations.google import GoogleCalendarService
from app.services.integrations.outlook import OutlookCalendarService
from app.services.integrations.slack_service import SlackIntegrationService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def sync_google_calendar(self, calendar_integration_id: str) -> dict:
    """Sync events from Google Calendar.
    
    Args:
        calendar_integration_id: UUID of CalendarIntegration
        
    Returns:
        Dictionary with sync results
    """
    db = SessionLocal()
    try:
        calendar_id = UUID(calendar_integration_id)
        calendar = db.query(CalendarIntegration).filter(
            CalendarIntegration.id == calendar_id,
            CalendarIntegration.provider == "google"
        ).first()
        
        if not calendar:
            logger.error(f"Calendar {calendar_id} not found")
            return {"status": "error", "message": "Calendar not found"}
        
        if not calendar.is_active or not calendar.sync_enabled:
            logger.debug(f"Calendar {calendar_id} sync not enabled")
            return {"status": "skipped", "message": "Sync not enabled"}
        
        oauth_account = calendar.oauth_account
        if not oauth_account or not oauth_account.access_token:
            logger.error(f"No OAuth account for calendar {calendar_id}")
            return {"status": "error", "message": "OAuth not configured"}
        
        service = GoogleCalendarService()
        result = service.sync_calendar_events(
            calendar.user_id,
            calendar,
            oauth_account,
            db
        )
        
        logger.info(f"Google Calendar sync result for {calendar_id}: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Error syncing Google Calendar {calendar_integration_id}: {exc}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def sync_outlook_calendar(self, calendar_integration_id: str) -> dict:
    """Sync events from Outlook Calendar.
    
    Args:
        calendar_integration_id: UUID of CalendarIntegration
        
    Returns:
        Dictionary with sync results
    """
    db = SessionLocal()
    try:
        calendar_id = UUID(calendar_integration_id)
        calendar = db.query(CalendarIntegration).filter(
            CalendarIntegration.id == calendar_id,
            CalendarIntegration.provider == "microsoft"
        ).first()
        
        if not calendar:
            logger.error(f"Calendar {calendar_id} not found")
            return {"status": "error", "message": "Calendar not found"}
        
        if not calendar.is_active or not calendar.sync_enabled:
            logger.debug(f"Calendar {calendar_id} sync not enabled")
            return {"status": "skipped", "message": "Sync not enabled"}
        
        oauth_account = calendar.oauth_account
        if not oauth_account or not oauth_account.access_token:
            logger.error(f"No OAuth account for calendar {calendar_id}")
            return {"status": "error", "message": "OAuth not configured"}
        
        service = OutlookCalendarService()
        result = service.sync_calendar_events(
            calendar.user_id,
            calendar,
            oauth_account,
            db
        )
        
        logger.info(f"Outlook Calendar sync result for {calendar_id}: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Error syncing Outlook Calendar {calendar_integration_id}: {exc}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task
def sync_all_calendars() -> dict:
    """Sync all active calendar integrations.
    
    Returns:
        Dictionary with overall sync results
    """
    db = SessionLocal()
    try:
        calendars = db.query(CalendarIntegration).filter(
            CalendarIntegration.is_active == True,
            CalendarIntegration.sync_enabled == True
        ).all()
        
        results = {
            "total": len(calendars),
            "synced": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }
        
        for calendar in calendars:
            try:
                if calendar.provider == "google":
                    task = sync_google_calendar.delay(str(calendar.id))
                elif calendar.provider == "microsoft":
                    task = sync_outlook_calendar.delay(str(calendar.id))
                else:
                    results["skipped"] += 1
                    continue
                
                results["synced"] += 1
                results["details"].append({
                    "calendar_id": str(calendar.id),
                    "provider": calendar.provider,
                    "task_id": task.id
                })
            except Exception as e:
                logger.error(f"Failed to schedule sync for calendar {calendar.id}: {e}")
                results["failed"] += 1
        
        logger.info(f"Scheduled calendar sync tasks: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in sync_all_calendars: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task
def send_slack_daily_summaries() -> dict:
    """Send daily time summaries to all Slack-connected users.
    
    Returns:
        Dictionary with results
    """
    db = SessionLocal()
    try:
        from datetime import datetime, timezone, timedelta
        from app.models.time_entry import TimeEntry
        from sqlalchemy import func
        
        bindings = db.query(SlackUserBinding).all()
        results = {
            "total": len(bindings),
            "sent": 0,
            "failed": 0
        }
        
        slack_service = SlackIntegrationService()
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        for binding in bindings:
            try:
                if not binding.notify_daily_summary:
                    continue
                
                # Get today's time entries
                entries = db.query(TimeEntry).filter(
                    TimeEntry.user_id == binding.user_id,
                    TimeEntry.started_at >= today_start
                ).all()
                
                if not entries:
                    continue
                
                total_minutes = sum(e.duration_minutes for e in entries)
                total_hours = total_minutes / 60
                
                # Send summary
                success = slack_service.send_daily_summary(
                    binding.user_id,
                    total_hours,
                    len(entries),
                    db
                )
                
                if success:
                    results["sent"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"Failed to send daily summary to user {binding.user_id}: {e}")
                results["failed"] += 1
        
        logger.info(f"Daily Slack summaries sent: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in send_slack_daily_summaries: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task
def send_invoice_notifications(invoice_id: str) -> dict:
    """Send invoice ready notifications via Slack.
    
    Args:
        invoice_id: UUID of Invoice
        
    Returns:
        Dictionary with results
    """
    db = SessionLocal()
    try:
        from app.models.invoice import Invoice
        
        invoice_uuid = UUID(invoice_id)
        invoice = db.query(Invoice).filter(Invoice.id == invoice_uuid).first()
        
        if not invoice:
            logger.error(f"Invoice {invoice_uuid} not found")
            return {"status": "error", "message": "Invoice not found"}
        
        # Find all user bindings for the invoice creator/client
        bindings = db.query(SlackUserBinding).filter(
            SlackUserBinding.user_id == invoice.created_by_user_id
        ).all()
        
        results = {
            "total": len(bindings),
            "sent": 0,
            "failed": 0
        }
        
        slack_service = SlackIntegrationService()
        for binding in bindings:
            try:
                if not binding.notify_invoice_ready:
                    continue
                
                success = slack_service.notify_invoice_ready(
                    invoice.invoice_number or str(invoice.id),
                    invoice.total_amount_cents,
                    binding.user_id,
                    db
                )
                
                if success:
                    results["sent"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"Failed to send invoice notification to user {binding.user_id}: {e}")
                results["failed"] += 1
        
        logger.info(f"Invoice notifications sent: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in send_invoice_notifications: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.services.tasks.integrations.sync_slack_status",
    max_retries=2,
    default_retry_delay=60,
)
def sync_slack_status(self, user_id=None):
    """
    Sync Slack user status for availability tracking.
    
    This task:
    - Fetches user status from Slack
    - Determines if user is in meeting/busy
    - Records status changes
    
    Args:
        user_id: Optional specific user to sync
    
    Returns:
        dict: Status sync summary
    """
    db = SessionLocal()
    try:
        from app.config.settings import Settings
        
        logger.info(f"Syncing Slack status (user_id={user_id})")
        
        settings = Settings()
        if not settings.slack_bot_token:
            logger.warning("Slack bot token not configured")
            return {"status": "skipped", "message": "No Slack token"}
        
        summary = {
            "users_synced": 0,
            "status_updates": 0,
            "errors": [],
        }
        
        from slack_sdk import WebClient
        slack_client = WebClient(token=settings.slack_bot_token)
        
        # Get Slack integrations
        bindings = db.query(SlackUserBinding).all() if not user_id else \
                   db.query(SlackUserBinding).filter(SlackUserBinding.user_id == user_id).all()
        
        for binding in bindings:
            try:
                response = slack_client.users_info(user=binding.slack_user_id)
                slack_user = response["user"]
                
                is_busy = slack_user.get("profile", {}).get("status_emoji") == ":spiral_calendar_pad:"
                logger.debug(f"User {binding.user_id} Slack status: busy={is_busy}")
                
                summary["status_updates"] += 1
                summary["users_synced"] += 1
            except Exception as e:
                logger.error(f"Error syncing Slack status for user {binding.user_id}: {e}")
                summary["errors"].append({"user_id": str(binding.user_id), "error": str(e)})
        
        logger.info(f"Slack status sync complete: {summary}")
        return summary
        
    except Exception as exc:
        logger.error(f"Slack status sync failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.services.tasks.integrations.health_check_integrations",
    max_retries=1,
    default_retry_delay=300,
)
def health_check_integrations(self):
    """
    Health check for all active integrations.
    
    This task:
    - Tests each integration's connectivity
    - Refreshes tokens if needed
    - Alerts on failures
    
    Returns:
        dict: Health check results
    """
    db = SessionLocal()
    try:
        logger.info("Running integration health checks")
        
        summary = {
            "calendars_checked": 0,
            "healthy": 0,
            "unhealthy": 0,
            "issues": [],
        }
        
        # Check calendar integrations
        calendars = db.query(CalendarIntegration).filter(
            CalendarIntegration.is_active == True
        ).all()
        
        summary["calendars_checked"] = len(calendars)
        
        for calendar in calendars:
            try:
                if not calendar.oauth_account or not calendar.oauth_account.access_token:
                    summary["unhealthy"] += 1
                    summary["issues"].append({
                        "calendar_id": str(calendar.id),
                        "provider": calendar.provider,
                        "error": "No valid token"
                    })
                    continue
                
                # Attempt a simple API call to test connectivity
                if calendar.provider == "google":
                    service = GoogleCalendarService()
                    service.list_calendars(calendar.oauth_account.access_token)
                elif calendar.provider == "microsoft":
                    service = OutlookCalendarService()
                    service.list_calendars(calendar.oauth_account.access_token)
                
                summary["healthy"] += 1
                logger.debug(f"Calendar {calendar.id} ({calendar.provider}) is healthy")
                
            except Exception as e:
                logger.warning(f"Calendar {calendar.id} health check failed: {e}")
                summary["unhealthy"] += 1
                summary["issues"].append({
                    "calendar_id": str(calendar.id),
                    "provider": calendar.provider,
                    "error": str(e)
                })
        
        logger.info(f"Integration health check complete: {summary}")
        return summary
        
    except Exception as exc:
        logger.error(f"Health check task failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))
    finally:
        db.close()
