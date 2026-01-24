"""CRUD service for TimeEntry model."""
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.time_entry import TimeEntry
from app.schemas.time_entry import TimeEntryCreate, TimeEntryUpdate


class TimeEntryService:
    """Service for TimeEntry CRUD operations."""

    @staticmethod
    def create(db: Session, entry_data: TimeEntryCreate, user_id: UUID) -> TimeEntry:
        """
        Create a new time entry.
        
        Args:
            db: Database session.
            entry_data: Time entry creation data.
            user_id: ID of user creating the entry.
            
        Returns:
            The created time entry.
        """
        # Calculate duration
        duration_ms = (entry_data.ended_at - entry_data.started_at).total_seconds()
        duration_minutes = int(duration_ms / 60)

        db_entry = TimeEntry(
            user_id=user_id,
            **entry_data.model_dump(),
            duration_minutes=duration_minutes,
        )
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        return db_entry

    @staticmethod
    def get_by_id(db: Session, entry_id: UUID) -> TimeEntry | None:
        """Get a time entry by ID."""
        return db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()

    @staticmethod
    def get_by_user(db: Session, user_id: UUID, skip: int = 0, limit: int = 50) -> list[TimeEntry]:
        """Get all time entries for a user."""
        return db.query(TimeEntry).filter(
            TimeEntry.user_id == user_id
        ).offset(skip).limit(limit).order_by(TimeEntry.started_at.desc()).all()

    @staticmethod
    def get_by_project(db: Session, project_id: UUID, skip: int = 0, limit: int = 50) -> list[TimeEntry]:
        """Get all time entries for a project."""
        return db.query(TimeEntry).filter(
            TimeEntry.project_id == project_id
        ).offset(skip).limit(limit).order_by(TimeEntry.started_at.desc()).all()

    @staticmethod
    def get_by_status(db: Session, status: str, skip: int = 0, limit: int = 50) -> list[TimeEntry]:
        """Get all time entries with a specific status."""
        return db.query(TimeEntry).filter(
            TimeEntry.status == status
        ).offset(skip).limit(limit).order_by(TimeEntry.started_at.desc()).all()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 50) -> list[TimeEntry]:
        """Get all time entries with pagination."""
        return db.query(TimeEntry).offset(skip).limit(limit).order_by(TimeEntry.started_at.desc()).all()

    @staticmethod
    def update(db: Session, entry_id: UUID, entry_data: TimeEntryUpdate) -> TimeEntry | None:
        """
        Update a time entry.
        
        Args:
            db: Database session.
            entry_id: ID of entry to update.
            entry_data: Updated entry data.
            
        Returns:
            The updated entry, or None if not found.
        """
        db_entry = TimeEntryService.get_by_id(db, entry_id)
        if not db_entry:
            return None

        update_data = entry_data.model_dump(exclude_unset=True)
        
        # Recalculate duration if timestamps changed
        if "started_at" in update_data or "ended_at" in update_data:
            started = update_data.get("started_at") or db_entry.started_at
            ended = update_data.get("ended_at") or db_entry.ended_at
            duration_ms = (ended - started).total_seconds()
            update_data["duration_minutes"] = int(duration_ms / 60)
        
        for key, value in update_data.items():
            setattr(db_entry, key, value)

        db.commit()
        db.refresh(db_entry)
        return db_entry

    @staticmethod
    def delete(db: Session, entry_id: UUID) -> bool:
        """
        Delete a time entry.
        
        Args:
            db: Database session.
            entry_id: ID of entry to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        db_entry = TimeEntryService.get_by_id(db, entry_id)
        if not db_entry:
            return False

        db.delete(db_entry)
        db.commit()
        return True

    @staticmethod
    def count_by_user(db: Session, user_id: UUID) -> int:
        """Get number of time entries for a user."""
        return db.query(TimeEntry).filter(TimeEntry.user_id == user_id).count()

    @staticmethod
    def total_minutes_by_user(db: Session, user_id: UUID) -> int:
        """Get total billable minutes for a user."""
        from sqlalchemy import func
        result = db.query(func.sum(TimeEntry.duration_minutes)).filter(
            TimeEntry.user_id == user_id,
            TimeEntry.status == "approved",
        ).scalar()
        return result or 0
