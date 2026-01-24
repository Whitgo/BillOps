from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.time_entry import TimeEntryCreate, TimeEntryResponse, TimeEntryUpdate
from app.services.time_entry import TimeEntryService

router = APIRouter(prefix="/time-entries", tags=["time_entries"])


@router.get("/", response_model=dict[str, object])
def list_time_entries(
    user_id: UUID | None = Query(None),
    project_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """List time entries with filtering and pagination."""
    if user_id:
        entries = TimeEntryService.get_by_user(db, user_id, skip=skip, limit=limit)
        total = TimeEntryService.count_by_user(db, user_id)
    elif project_id:
        entries = TimeEntryService.get_by_project(db, project_id, skip=skip, limit=limit)
        total = len(entries)
    elif status_filter:
        entries = TimeEntryService.get_by_status(db, status_filter, skip=skip, limit=limit)
        total = len(entries)
    else:
        entries = TimeEntryService.get_all(db, skip=skip, limit=limit)
        total = len(entries)
    return {
        "items": entries,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/", response_model=TimeEntryResponse, status_code=status.HTTP_201_CREATED)
def create_time_entry(
    data: TimeEntryCreate,
    db: Session = Depends(get_db),
) -> TimeEntryResponse:
    """Create a new time entry."""
    entry = TimeEntryService.create(db, data)
    return TimeEntryResponse.model_validate(entry)


@router.get("/{entry_id}", response_model=TimeEntryResponse)
def get_time_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
) -> TimeEntryResponse:
    """Get a time entry by ID."""
    entry = TimeEntryService.get_by_id(db, entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time entry not found",
        )
    return TimeEntryResponse.model_validate(entry)


@router.patch("/{entry_id}", response_model=TimeEntryResponse)
def update_time_entry(
    entry_id: UUID,
    data: TimeEntryUpdate,
    db: Session = Depends(get_db),
) -> TimeEntryResponse:
    """Update a time entry."""
    entry = TimeEntryService.update(db, entry_id, data)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time entry not found",
        )
    return TimeEntryResponse.model_validate(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_time_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete a time entry."""
    success = TimeEntryService.delete(db, entry_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time entry not found",
        )
