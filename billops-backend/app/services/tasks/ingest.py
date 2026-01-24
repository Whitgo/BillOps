"""
Celery task for ingesting and processing raw activity signals.

Converts activity events from integrations into suggested time entries.
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.celery_app import celery as celery_app
from app.db.session import SessionLocal
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.schemas.time_entry import TimeEntryCreate
from app.services.time_capture.heuristics import ActivityHeuristics
from app.services.time_entry import TimeEntryService


logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.ingest_events", bind=True, max_retries=3)
def ingest_events_task(self, user_id: str, activity_signals: list[dict]) -> dict:
    """
    Process raw activity signals and create suggested time entries.
    
    Args:
        user_id: UUID of user who generated signals
        activity_signals: List of activity signal dicts with timestamp and metadata
        
    Returns:
        Dict with processing results and created time entry IDs
    """
    db = SessionLocal()
    try:
        logger.info(f"Ingesting {len(activity_signals)} signals for user {user_id}")
        
        # Validate user exists
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            return {"status": "error", "message": f"User {user_id} not found"}
        
        # Convert timestamps to datetime objects if needed
        processed_signals = []
        for signal in activity_signals:
            ts = signal.get("timestamp")
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            elif isinstance(ts, (int, float)):
                ts = datetime.fromtimestamp(ts, tz=timezone.utc)
            
            signal_copy = signal.copy()
            signal_copy["timestamp"] = ts
            processed_signals.append(signal_copy)
        
        # Generate suggested time entries
        suggested_entries = ActivityHeuristics.generate_time_entries(processed_signals)
        
        if not suggested_entries:
            logger.info(f"No suggested time entries generated for user {user_id}")
            return {
                "status": "success",
                "suggested_count": 0,
                "created_ids": [],
                "verification_required": [],
            }
        
        logger.info(f"Generated {len(suggested_entries)} suggested entries")
        
        # Create time entries
        created_ids = []
        verification_required = []
        
        for suggested in suggested_entries:
            try:
                # Find project and client from context
                project_id = suggested.context_data.get("project_id")
                client_id = suggested.context_data.get("client_id")
                
                # Skip if no project/client (will be marked for manual classification)
                if not project_id or not client_id:
                    verification_required.append({
                        "reason": "missing_project_or_client",
                        "started_at": suggested.started_at.isoformat(),
                        "ended_at": suggested.ended_at.isoformat(),
                    })
                    continue
                
                # Create time entry
                entry_data = TimeEntryCreate(
                    project_id=UUID(project_id) if isinstance(project_id, str) else project_id,
                    client_id=UUID(client_id) if isinstance(client_id, str) else client_id,
                    billing_rule_id=None,
                    source="auto",  # Indicates automated ingestion
                    started_at=suggested.started_at,
                    ended_at=suggested.ended_at,
                    description=suggested.description,
                    context_data=suggested.context_data,
                )
                
                # Create entry with pending status
                db_entry = TimeEntry(
                    **entry_data.model_dump(),
                    user_id=UUID(user_id),
                    status="pending",  # Requires review
                    duration_minutes=int((suggested.ended_at - suggested.started_at).total_seconds() / 60),
                )
                db.add(db_entry)
                db.flush()
                
                created_ids.append(str(db_entry.id))
                
                # Mark for verification if low confidence
                if suggested.should_verify:
                    verification_required.append({
                        "entry_id": str(db_entry.id),
                        "reason": "low_confidence",
                        "confidence": suggested.confidence,
                    })
                
            except Exception as e:
                logger.error(f"Error creating time entry: {e}", exc_info=True)
                verification_required.append({
                    "reason": "error_creating_entry",
                    "error": str(e),
                })
        
        db.commit()
        
        logger.info(f"Created {len(created_ids)} time entries, {len(verification_required)} require verification")
        
        return {
            "status": "success",
            "suggested_count": len(suggested_entries),
            "created_count": len(created_ids),
            "created_ids": created_ids,
            "verification_required": verification_required,
        }
    
    except Exception as e:
        logger.error(f"Error in ingest_events_task: {e}", exc_info=True)
        
        # Retry with exponential backoff
        try:
            self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except Exception as retry_err:
            logger.error(f"Task retry failed: {retry_err}")
            return {
                "status": "error",
                "message": str(e),
                "retried": True,
            }
    
    finally:
        db.close()
