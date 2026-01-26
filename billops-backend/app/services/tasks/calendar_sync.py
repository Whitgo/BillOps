"""Celery tasks for calendar synchronization."""
import logging
from datetime import datetime, timezone

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.integrations import CalendarIntegration
from app.models.user import UserOAuthAccount
from app.services.integrations.google import GoogleCalendarService
from app.services.integrations.outlook import OutlookCalendarService

logger = logging.getLogger(__name__)


@celery_app.task(name="calendar:sync_all")
def sync_all_calendars():
    """Sync all active calendar integrations."""
    db = SessionLocal()
    try:
        # Get all active calendar integrations
        calendars = db.query(CalendarIntegration).filter(
            CalendarIntegration.is_active == True,
            CalendarIntegration.sync_enabled == True,
        ).all()
        
        logger.info(f"Starting sync for {len(calendars)} calendars")
        
        for calendar in calendars:
            try:
                sync_single_calendar(calendar.id)
            except Exception as e:
                logger.error(f"Failed to sync calendar {calendar.id}: {e}")
        
        logger.info("Calendar sync completed")
        return {"status": "success", "synced_calendars": len(calendars)}
    finally:
        db.close()


@celery_app.task(name="calendar:sync_single")
def sync_single_calendar(calendar_id: str):
    """Sync a single calendar."""
    db = SessionLocal()
    try:
        calendar = db.query(CalendarIntegration).filter(
            CalendarIntegration.id == calendar_id,
            CalendarIntegration.is_active == True,
            CalendarIntegration.sync_enabled == True,
        ).first()
        
        if not calendar:
            logger.warning(f"Calendar {calendar_id} not found or not active")
            return {"status": "error", "message": "Calendar not found"}
        
        # Get OAuth account
        oauth_account = calendar.oauth_account
        if not oauth_account:
            logger.error(f"No OAuth account for calendar {calendar_id}")
            return {"status": "error", "message": "No OAuth account"}
        
        # Check if token needs refresh
        if oauth_account.access_token_expires_at:
            if oauth_account.access_token_expires_at <= datetime.now(timezone.utc):
                logger.info(f"Token expired for calendar {calendar_id}, refreshing...")
        
        # Sync based on provider
        if calendar.provider == "google":
            service = GoogleCalendarService()
            result = service.sync_calendar_events(
                calendar.user_id,
                calendar,
                oauth_account,
                db
            )
        elif calendar.provider == "microsoft":
            service = OutlookCalendarService()
            result = service.sync_calendar_events(
                calendar.user_id,
                calendar,
                oauth_account,
                db
            )
        else:
            logger.error(f"Unknown provider: {calendar.provider}")
            return {"status": "error", "message": f"Unknown provider: {calendar.provider}"}
        
        logger.info(f"Synced calendar {calendar_id}: {result}")
        return result
    except Exception as e:
        logger.error(f"Error syncing calendar {calendar_id}: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="calendar:refresh_tokens")
def refresh_all_tokens():
    """Refresh all expired OAuth tokens."""
    db = SessionLocal()
    try:
        # Get all OAuth accounts with refresh tokens
        oauth_accounts = db.query(UserOAuthAccount).filter(
            UserOAuthAccount.refresh_token.isnot(None),
        ).all()
        
        logger.info(f"Checking {len(oauth_accounts)} OAuth accounts for token refresh")
        
        refreshed_count = 0
        for account in oauth_accounts:
            try:
                if account.access_token_expires_at:
                    if account.access_token_expires_at <= datetime.now(timezone.utc):
                        # Token is expired, refresh it
                        calendars = db.query(CalendarIntegration).filter(
                            CalendarIntegration.oauth_account_id == account.id
                        ).all()
                        
                        if calendars:
                            # Determine provider from calendar
                            provider = calendars[0].provider
                            
                            if provider == "google":
                                service = GoogleCalendarService()
                                service.refresh_access_token(account, db)
                                refreshed_count += 1
                                logger.info(f"Refreshed token for user {account.user_id}")
                            elif provider == "microsoft":
                                service = OutlookCalendarService()
                                service.refresh_access_token(account, db)
                                refreshed_count += 1
                                logger.info(f"Refreshed token for user {account.user_id}")
            except Exception as e:
                logger.error(f"Error refreshing token for account {account.id}: {e}")
        
        logger.info(f"Token refresh completed: {refreshed_count} tokens refreshed")
        return {"status": "success", "refreshed_count": refreshed_count}
    finally:
        db.close()
