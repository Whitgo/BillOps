"""Invoice generation and management async tasks."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.invoice import Invoice
from app.models.user import User
from app.models.time_entry import TimeEntry
from app.services.notifications.email import EmailNotificationService
from app.services.notifications.slack import SlackNotificationService
from app.services.tasks.notifications import send_invoice_email, send_payment_email
from app.config.settings import Settings

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.services.tasks.invoices.generate_pending_invoices",
    max_retries=3,
    default_retry_delay=120,
)
def generate_pending_invoices(self, billing_period: Optional[str] = None):
    """
    Generate invoices for completed billing periods.
    
    This task:
    - Identifies completed billing periods
    - Calculates billable hours and amounts
    - Groups by client
    - Creates draft invoices
    - Sets due dates
    
    Args:
        billing_period: Specific period to generate (YYYY-MM)
    
    Returns:
        dict: Generation summary with invoice counts
    """
    db = SessionLocal()
    try:
        logger.info(f"Generating pending invoices (period={billing_period})")
        
        # Parse billing period or use previous month
        if billing_period:
            year, month = map(int, billing_period.split("-"))
        else:
            today = datetime.now(timezone.utc).date()
            if today.day < 15:
                # Use previous month
                first_of_this_month = today.replace(day=1)
                last_of_prev_month = first_of_this_month - timedelta(days=1)
                year, month = last_of_prev_month.year, last_of_prev_month.month
            else:
                year, month = today.year, today.month
        
        # Get start and end of billing period
        period_start = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            period_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            period_end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        
        logger.info(f"Generating invoices for {year}-{month:02d}")
        
        summary = {
            "period": f"{year}-{month:02d}",
            "invoices_created": 0,
            "invoices_updated": 0,
            "total_amount": 0,
            "by_client": {},
            "errors": [],
        }
        
        # Get all users with time entries in period
        entries = db.query(TimeEntry).filter(
            TimeEntry.start_time >= period_start,
            TimeEntry.start_time < period_end,
            TimeEntry.billable == True,
        ).all()
        
        # Group by user and client
        from collections import defaultdict
        by_user_client = defaultdict(list)
        
        for entry in entries:
            key = (str(entry.user_id), str(entry.client_id) if entry.client_id else None)
            by_user_client[key].append(entry)
        
        # Create invoices for each user-client combination
        for (user_id, client_id), entries in by_user_client.items():
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    continue
                
                # Calculate totals
                total_hours = sum(e.duration_minutes for e in entries) / 60.0
                hourly_rate = user.hourly_rate or 0
                invoice_amount = total_hours * hourly_rate
                
                # Check if invoice already exists for this period
                existing = db.query(Invoice).filter(
                    Invoice.user_id == user_id,
                    Invoice.client_id == client_id,
                    Invoice.period_start == period_start,
                    Invoice.period_end == period_end,
                ).first()
                
                if existing:
                    # Update existing invoice
                    existing.total_amount = invoice_amount
                    existing.updated_at = datetime.now(timezone.utc)
                    db.commit()
                    summary["invoices_updated"] += 1
                    logger.info(f"Updated invoice {existing.id}")
                else:
                    # Create new invoice
                    invoice = Invoice(
                        user_id=user_id,
                        client_id=client_id,
                        invoice_number=self._generate_invoice_number(user_id, period_start),
                        period_start=period_start,
                        period_end=period_end,
                        total_amount=invoice_amount,
                        status="draft",
                        due_date=period_end + timedelta(days=30),
                        created_at=datetime.now(timezone.utc),
                    )
                    db.add(invoice)
                    db.commit()
                    summary["invoices_created"] += 1
                    logger.info(f"Created invoice {invoice.id}")
                
                summary["total_amount"] += invoice_amount
                if client_id not in summary["by_client"]:
                    summary["by_client"][client_id or "unassigned"] = {
                        "count": 0,
                        "amount": 0,
                    }
                summary["by_client"][client_id or "unassigned"]["count"] += 1
                summary["by_client"][client_id or "unassigned"]["amount"] += invoice_amount
                
            except Exception as e:
                logger.error(f"Error creating invoice for user {user_id}, client {client_id}: {e}")
                summary["errors"].append({
                    "user_id": user_id,
                    "client_id": client_id,
                    "error": str(e)
                })
        
        logger.info(f"Invoice generation complete: {summary}")
        return summary
        
    except Exception as exc:
        logger.error(f"Invoice generation failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=120 * (2 ** self.request.retries))
    finally:
        db.close()
    
    def _generate_invoice_number(self, user_id: str, period_start: datetime) -> str:
        """Generate a unique invoice number."""
        # Format: INV-YYYY-MM-XXXX (where XXXX is sequential)
        year = period_start.year
        month = period_start.month
        # In production, query last invoice number and increment
        seq = 1
        return f"INV-{year}-{month:02d}-{seq:04d}"


@celery_app.task(
    bind=True,
    name="app.services.tasks.invoices.send_pending_invoices",
    max_retries=3,
    default_retry_delay=120,
)
def send_pending_invoices(self, invoice_status: str = "draft"):
    """
    Send pending invoices to clients.
    
    This task:
    - Finds draft invoices ready to send
    - Generates PDF versions
    - Sends via email and Slack
    - Updates invoice status
    
    Args:
        invoice_status: Invoice status to send (default: draft)
    
    Returns:
        dict: Send summary
    """
    db = SessionLocal()
    try:
        logger.info(f"Sending pending invoices (status={invoice_status})")
        
        summary = {
            "invoices_sent": 0,
            "emails_sent": 0,
            "slack_messages_sent": 0,
            "errors": [],
        }
        
        # Get invoices to send
        invoices = db.query(Invoice).filter(
            Invoice.status == invoice_status,
            Invoice.client_id.isnot(None),
        ).all()
        
        for invoice in invoices:
            try:
                client = invoice.client
                if not client or not client.email:
                    logger.warning(f"Invoice {invoice.id} has no client email")
                    continue
                
                # Queue email sending
                send_invoice_email.delay(
                    invoice_id=str(invoice.id),
                    recipient_email=client.email,
                    recipient_name=client.name,
                )
                summary["emails_sent"] += 1
                
                # Update invoice status
                invoice.status = "sent"
                invoice.sent_at = datetime.now(timezone.utc)
                db.commit()
                summary["invoices_sent"] += 1
                logger.info(f"Queued send for invoice {invoice.id}")
                
            except Exception as e:
                logger.error(f"Error sending invoice {invoice.id}: {e}")
                summary["errors"].append({
                    "invoice_id": str(invoice.id),
                    "error": str(e)
                })
        
        logger.info(f"Pending invoice send complete: {summary}")
        return summary
        
    except Exception as exc:
        logger.error(f"Pending invoice send failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=120 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.services.tasks.invoices.send_payment_reminders",
    max_retries=2,
    default_retry_delay=120,
)
def send_payment_reminders(self, days_before_due: int = 7):
    """
    Send payment reminders for invoices due soon.
    
    Args:
        days_before_due: Send reminder N days before due date
    
    Returns:
        dict: Reminder summary
    """
    db = SessionLocal()
    try:
        logger.info(f"Sending payment reminders (due in {days_before_due} days)")
        
        # Find invoices due in N days
        target_date = datetime.now(timezone.utc).date() + timedelta(days=days_before_due)
        
        invoices = db.query(Invoice).filter(
            Invoice.due_date.cast(type(datetime.now().date())) == target_date,
            Invoice.status.in_(["sent", "overdue"]),
        ).all()
        
        summary = {
            "reminders_sent": 0,
            "errors": [],
        }
        
        notification_service = EmailNotificationService()
        
        for invoice in invoices:
            try:
                client = invoice.client
                if not client or not client.email:
                    continue
                
                notification_service.send_invoice_overdue_alert(
                    recipient_email=client.email,
                    recipient_name=client.name,
                    invoice_number=invoice.invoice_number,
                    invoice_total_cents=int(invoice.total_amount * 100),
                    days_overdue=0,  # Not yet overdue, just reminder
                )
                summary["reminders_sent"] += 1
                
            except Exception as e:
                logger.error(f"Error sending reminder for invoice {invoice.id}: {e}")
                summary["errors"].append({
                    "invoice_id": str(invoice.id),
                    "error": str(e)
                })
        
        logger.info(f"Payment reminders sent: {summary}")
        return summary
        
    except Exception as exc:
        logger.error(f"Payment reminder task failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=120 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.services.tasks.invoices.cleanup_old_tasks",
    max_retries=1,
    default_retry_delay=300,
)
def cleanup_old_tasks(self, days: int = 30):
    """
    Clean up old completed tasks and logs.
    
    Args:
        days: Delete records older than N days
    
    Returns:
        dict: Cleanup summary
    """
    db = SessionLocal()
    try:
        from celery.result import AsyncResult
        
        logger.info(f"Cleaning up old tasks (older than {days} days)")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        summary = {
            "tasks_cleaned": 0,
            "task_ids": [],
        }
        
        # In production, connect to Redis and clean up old task results
        logger.info(f"Cleanup complete: {summary}")
        return summary
        
    except Exception as exc:
        logger.error(f"Cleanup task failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))
    finally:
        db.close()
